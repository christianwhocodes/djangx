#!/usr/bin/env python3
"""
Simple script to bump version, tag, and push to git.
Usage:
    uv run python scripts/publish.py --test         # Bump patch version, tag as dev-X.X.X, push
    uv run python scripts/publish.py --prod         # Bump patch version, tag as vX.X.X, push
    uv run python scripts/publish.py --bump-only    # Just bump version without pushing
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

from termcolor import colored


def run_command(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run shell command"""
    print(colored(f"▶ {cmd}", "cyan"))
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(colored(f"❌ Command failed: {result.stderr}", "red"))
        sys.exit(1)
    return result


def get_pyproject_path() -> Path:
    """Get the path to pyproject.toml"""
    return Path(__file__).resolve().parent / "pyproject.toml"


def get_current_version() -> str:
    """Extract version from pyproject.toml"""
    pyproject = get_pyproject_path()
    content = pyproject.read_text()
    match = re.search(r'version = "([^"]+)"', content)
    if not match:
        print(colored("❌ Could not find version in pyproject.toml", "red"))
        sys.exit(1)
    return match.group(1)


def bump_version(version: str, bump_type: str = "patch") -> str:
    """
    Bump version number.

    Expects a semantic version string like "0.1.2" and increments according to bump_type.
    """
    parts = version.split(".")
    if len(parts) != 3:
        print(colored(f"❌ Invalid version format: {version}. Expected X.Y.Z", "red"))
        sys.exit(1)

    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

    match bump_type:
        case "major":
            return f"{major + 1}.0.0"
        case "minor":
            return f"{major}.{minor + 1}.0"
        case _:  # patch
            return f"{major}.{minor}.{patch + 1}"


def confirm_version_bump(current: str, new: str) -> str:
    """Ask user to confirm version bump, exit if declined"""
    response = input(
        colored(f"\n❓ Bump version from {current} to {new}? (y/n): ", "yellow")
    )

    return response.lower()


def update_version_and_sync(new_version: str) -> None:
    """Update version in pyproject.toml"""
    pyproject = get_pyproject_path()
    content = pyproject.read_text()
    updated = re.sub(r'version = "[^"]+"', f'version = "{new_version}"', content)
    pyproject.write_text(updated)
    print(colored(f"✅ Updated version to {new_version}", "green"))
    print(colored("\n🔄 Syncing dependencies...", "blue"))
    run_command("uv sync")


def git_stage_and_commit(new_version: str) -> None:
    """Check for changes and stage appropriate files"""
    print(colored("\n📋 Checking for uncommitted changes...", "blue"))
    status = run_command("git status --porcelain", check=False)

    has_other_changes = bool(status.stdout.strip())
    if not has_other_changes:
        run_command("git add pyproject.toml uv.lock")
        print(colored("✅ No other changes detected", "green"))
        return

    print(colored("\n⚠️  You have uncommitted changes:", "yellow"))
    print(status.stdout)
    commit_all = input(
        colored("\n❓ Include all changes in this version commit? (y/n): ", "yellow")
    )

    if commit_all.lower() == "y":
        run_command("git add -A")
        print(colored("✅ All changes will be included", "green"))
    else:
        run_command("git add pyproject.toml uv.lock")
        print(colored("✅ Only version files will be included", "green"))

    run_command(f'git commit -m "Bump version to {new_version}"')


def create_and_push_tag(new_version: str, is_test: bool) -> None:
    """Create git tag and push to remote"""
    tag = f"dev-{new_version}" if is_test else f"v{new_version}"
    target = "TestPyPI" if is_test else "PyPI"

    print(colored(f"\n🏷️  Creating tag: {tag} (will publish to {target})", "blue"))

    run_command(f"git tag {tag}")
    run_command("git push")
    run_command(f"git push origin {tag}")

    print(colored(f"\n✅ Done! GitHub Actions will now publish to {target}", "green"))
    print(
        colored(
            "📊 Check progress: https://github.com/christianwhocodes/tawala/actions",
            "cyan",
        )
    )


def parse_and_validate_arguments() -> argparse.Namespace:
    """Parse and validate command line arguments"""
    parser = argparse.ArgumentParser(description="Bump version and publish")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Publish to TestPyPI (dev- tag)",
    )
    parser.add_argument(
        "--prod",
        action="store_true",
        help="Publish to PyPI (v tag)",
    )
    parser.add_argument(
        "--bump-only",
        action="store_true",
        help="Only bump version, don't tag/push",
    )
    parser.add_argument(
        "--bump-type",
        type=str,
        choices=["major", "minor", "patch"],
        default="patch",
        help="Type of version bump (major, minor, patch). Default is patch",
    )

    args = parser.parse_args()

    # Validate that at least one mode is specified
    if not (args.test or args.prod or args.bump_only):
        parser.error("Please specify --test, --prod, or --bump-only")

    return args


def main() -> None:
    args = parse_and_validate_arguments()

    # Get versions
    current_version = get_current_version()
    new_version = bump_version(current_version, args.bump_type)

    print(colored(f"📦 Current version: {current_version}", "blue"))
    print(colored(f"📦 New version: {new_version}", "blue"))

    # Confirm with user
    if confirm_version_bump(current_version, new_version) != "y":
        print(colored("❌ Aborted", "red"))
        sys.exit(0)
    else:
        update_version_and_sync(new_version)
        git_stage_and_commit(new_version)
        if args.bump_only:
            print(colored("\n✅ Version bumped. Push manually with: git push", "green"))
        else:
            create_and_push_tag(new_version, is_test=args.test)


if __name__ == "__main__":
    main()
