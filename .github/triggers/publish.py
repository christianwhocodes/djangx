"""Trigger the 'Publish to PyPI' GitHub Actions workflow by tagging and pushing.

This script:
- Reads repository metadata from pyproject.toml to build the Actions URL.
- Obtains the current version via the `uv` CLI (`uv version --short`).
- Creates an annotated git tag named "v{version}" and pushes tags to origin,
    which triggers the workflow defined in .github/workflows/publish.yaml
    (configured to run on push tags and workflow_dispatch).

Run with --dry or --dry-run to preview the git commands without executing them.
"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from pathlib import Path
from subprocess import CalledProcessError, CompletedProcess, run
from sys import exit
from tomllib import TOMLDecodeError, load
from typing import Any, NoReturn, Optional
from urllib.parse import urlparse

from christianwhocodes.colors import Text, colored_print
from christianwhocodes.helpers import ExitCode


class ProjectConfig:
    """Read and cache project metadata from pyproject.toml"""

    pyproject_path: Path
    _config: Optional[dict[str, Any]]

    def __init__(self, pyproject_path: Path) -> None:
        self.pyproject_path = pyproject_path
        self._config = None

    @classmethod
    def from_base_dir(cls) -> "ProjectConfig":
        """Factory constructor using the project root directory"""
        base = Path(__file__).resolve().parent.parent.parent
        return cls(base / "pyproject.toml")

    @property
    def repo_url(self) -> str:
        """Return repository URL from TOML (raises ValueError if missing)."""
        if self._config is None:
            with open(self.pyproject_path, "rb") as f:
                self._config = load(f)

        urls = self._config.get("project", {}).get("urls", {})
        url = urls.get("repository")
        if not url:
            raise ValueError("No repository URL found in project.urls")
        return url

    def sanitize_repo_path(self) -> str:
        """Strip trailing slashes and `.git` suffix."""
        path = self.repo_url.rstrip("/")
        if path.endswith(".git"):
            path = path[:-4]
        return path

    def build_actions_url(self) -> str:
        """Convert repo URL into GitHub Actions page URL; raises ValueError if not GitHub."""
        parsed = urlparse(self.sanitize_repo_path())
        if "github.com" not in parsed.netloc:
            raise ValueError("Repository URL is not a GitHub URL")
        return f"https://{parsed.netloc}{parsed.path}/actions"

    def fetch_version(self) -> str:
        """Get version from `uv` CLI. Raises CalledProcessError or ValueError."""
        result: CompletedProcess[str] = run(
            ["uv", "version", "--short"],
            check=True,
            capture_output=True,
            text=True,
        )
        version = result.stdout.strip()
        if not version:
            raise ValueError("Version output was empty")
        return version


class GitPublisher:
    """Encapsulate git tagging and pushing"""

    config: ProjectConfig

    def __init__(self, config: ProjectConfig) -> None:
        self.config = config

    def tag(self, version: str, dry: bool) -> str:
        """Create git tag and return tag string (e.g. 'v1.2.3')."""
        tag = f"v{version}"
        cmd = ["git", "tag", "-a", tag, "-m", f"Release {version}"]

        if dry:
            colored_print(f"Would run: {' '.join(cmd)}", Text.WARNING)
        else:
            run(cmd, check=True, capture_output=True, text=True)

        return tag

    def push(self, dry: bool) -> None:
        """Push tags to origin."""
        cmd = ["git", "push", "origin", "--tags"]
        if dry:
            colored_print("Would run: git push origin --tags", Text.WARNING)
        else:
            run(cmd, check=True, capture_output=True, text=True)


def tag_and_push(dry_run: bool = False) -> ExitCode:
    if dry_run:
        colored_print("DRY RUN MODE - no changes will be made\n", Text.INFO)

    try:
        cfg = ProjectConfig.from_base_dir()
        version = cfg.fetch_version()
        actions_url = cfg.build_actions_url()

        pub = GitPublisher(cfg)
        tag = pub.tag(version, dry_run)
        pub.push(dry_run)

    except FileNotFoundError as e:
        # e.filename can be None; guard for that
        filename = getattr(e, "filename", None)
        if filename:
            colored_print(f"File not found: {filename}", Text.ERROR)
        else:
            colored_print("File not found", Text.ERROR)
        return ExitCode.ERROR

    except CalledProcessError as e:
        # e.cmd may be list[str] or None; format defensively
        cmd = " ".join(map(str, e.cmd)) if e.cmd else "<cmd>"
        colored_print(f"Command failed: {cmd}", Text.ERROR)
        colored_print(f"Return code: {e.returncode}", Text.ERROR)
        if getattr(e, "stdout", None):
            colored_print(f"stdout: {e.stdout}", Text.ERROR)
        if getattr(e, "stderr", None):
            colored_print(f"stderr: {e.stderr}", Text.ERROR)
        return ExitCode.ERROR

    except TOMLDecodeError as e:
        colored_print(f"Failed to parse pyproject.toml: {str(e)}", Text.ERROR)
        return ExitCode.ERROR

    except ValueError as e:
        colored_print(f"Configuration error: {str(e)}", Text.ERROR)
        return ExitCode.ERROR

    except Exception as e:
        colored_print(f"Unexpected error: {str(e)}", Text.ERROR)
        return ExitCode.ERROR

    else:
        if dry_run:
            colored_print(f"Tag {tag} would be pushed successfully.", Text.SUCCESS)
            colored_print("GitHub Actions workflow would trigger.", Text.SUCCESS)
        else:
            colored_print(f"Tag {tag} pushed successfully!", Text.SUCCESS)
            colored_print(
                [("Monitor workflow: ", Text.INFO), (actions_url, Text.HIGHLIGHT)]
            )

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
