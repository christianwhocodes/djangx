"""Trigger the 'Publish to PyPI' GitHub Actions workflow by tagging and pushing.

This script:
- Reads repository metadata from pyproject.toml to build the Actions URL.
- Obtains the current version from pyproject.toml.
- Creates an annotated git tag named "v{version}" and pushes tags to origin,
    which triggers the workflow defined in .github/workflows/publish.yaml
    (configured to run on push tags and workflow_dispatch).

Run with --dry or --dry-run to preview the git commands without executing them.
"""

from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from pathlib import Path
from subprocess import CalledProcessError, run
from sys import exit
from tomllib import TOMLDecodeError
from typing import NoReturn
from urllib.parse import urlparse

from christianwhocodes.utils import ExitCode, PyProject, Text, print


class GitPublisher:
    """Encapsulate git tagging and pushing"""

    def __init__(self, pyproject: PyProject) -> None:
        self.project = pyproject

    # ---------------------------------------------------------
    #   REPO URL EXTRACTION (FIXED)
    # ---------------------------------------------------------
    def _get_repo_url(self) -> str:
        """
        Return repository URL from pyproject.toml (raises KeyError if missing).

        Supports:
        - https://github.com/user/repo
        - https://github.com/user/repo.git
        - git@github.com:user/repo.git
        """
        urls = self.project.data.get("project", {}).get("urls", {})
        url = urls.get("repository")

        if not url:
            raise KeyError("No repository URL found in project.urls")

        return url

    def _normalize_repo_url(self, raw: str) -> str:
        """
        Normalize Git remote URL into a uniform `https://github.com/user/repo`
        format so we can build an Actions URL.

        Handles:
        - git@github.com:user/repo.git
        - https://github.com/user/repo
        - https://github.com/user/repo.git
        """

        raw = raw.strip()

        # SSH-style: git@github.com:user/repo.git
        if raw.startswith("git@github.com:"):
            repo = raw.replace("git@github.com:", "")
            repo = repo.removesuffix(".git")
            return f"https://github.com/{repo}"

        parsed = urlparse(raw)

        # HTTPS URL but may have trailing .git or /
        if "github.com" in parsed.netloc:
            path = parsed.path.rstrip("/").removesuffix(".git")
            return f"https://github.com{path}"

        raise ValueError("Repository URL is not a GitHub URL")

    def build_actions_url(self) -> str:
        """
        Build the GitHub Actions URL:

          https://github.com/user/repo/actions
        """
        repo_url = self._get_repo_url()
        norm = self._normalize_repo_url(repo_url)
        return f"{norm}/actions"

    # ---------------------------------------------------------
    #   GIT OPERATIONS
    # ---------------------------------------------------------
    def tag(self, version: str, dry: bool) -> str:
        """Create git tag and return tag string (e.g. 'v1.2.3')."""
        tag = f"v{version}"
        cmd = ["git", "tag", "-a", tag, "-m", f"Release {version}"]

        if dry:
            print(f"Would run: {' '.join(cmd)}", Text.WARNING)
        else:
            run(cmd, check=True, capture_output=True, text=True)

        return tag

    def push(self, dry: bool) -> None:
        """Push tags to origin."""
        cmd = ["git", "push", "origin", "--tags"]
        if dry:
            print("Would run: git push origin --tags", Text.WARNING)
        else:
            run(cmd, check=True, capture_output=True, text=True)


# =========================================================
#   MAIN FLOW
# =========================================================
def tag_and_push(dry_run: bool = False) -> ExitCode:
    if dry_run:
        print("DRY RUN MODE - no changes will be made\n", Text.INFO)

    try:
        pyproject = PyProject(Path(__file__).resolve().parent.parent.parent / "pyproject.toml")

        version = pyproject.version

        pub = GitPublisher(pyproject)
        actions_url = pub.build_actions_url()

        tag = pub.tag(version, dry_run)
        pub.push(dry_run)

    except FileNotFoundError as e:
        filename = getattr(e, "filename", None)
        print(f"File not found: {filename or ''}".strip(), Text.ERROR)
        return ExitCode.ERROR

    except CalledProcessError as e:
        cmd = " ".join(map(str, e.cmd)) if e.cmd else "<cmd>"
        print(f"Command failed: {cmd}", Text.ERROR)
        print(f"Return code: {e.returncode}", Text.ERROR)
        if getattr(e, "stdout", None):
            print(f"stdout: {e.stdout}", Text.ERROR)
        if getattr(e, "stderr", None):
            print(f"stderr: {e.stderr}", Text.ERROR)
        return ExitCode.ERROR

    except TOMLDecodeError as e:
        print(f"Failed to parse pyproject.toml: {str(e)}", Text.ERROR)
        return ExitCode.ERROR

    except (KeyError, ValueError) as e:
        print(f"Configuration error: {str(e)}", Text.ERROR)
        return ExitCode.ERROR

    except Exception as e:
        print(f"Unexpected error: {str(e)}", Text.ERROR)
        return ExitCode.ERROR

    else:
        if dry_run:
            print(f"Tag {tag} would be pushed successfully.", Text.SUCCESS)
            print("GitHub Actions workflow would trigger.", Text.SUCCESS)
        else:
            print(f"Tag {tag} pushed successfully!", Text.SUCCESS)
            print([("Monitor workflow: ", Text.INFO), (actions_url, Text.HIGHLIGHT)])

        return ExitCode.SUCCESS


def main() -> NoReturn:
    parser = ArgumentParser(
        description="Create and push git tag to trigger publishing workflow",
        formatter_class=RawDescriptionHelpFormatter,
        epilog="Example:\n  publish.py --dry-run",
    )

    parser.add_argument(
        "--dry",
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Preview commands without execution",
    )

    args: Namespace = parser.parse_args()
    exit(tag_and_push(args.dry_run))


if __name__ == "__main__":
    main()
