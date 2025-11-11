#!/usr/bin/env python3
"""
Simple script to bump version, tag, and push to git.
Usage:
    uv run python publish.py --target testpypi    # Bump version, tag as dev-X.X.X, push, publish to TestPyPI via GitHub Actions
    uv run python publish.py --target pypi        # Bump version, tag as vX.X.X, push, publish to PyPI via GitHub Actions (default)
    uv run python publish.py --bump-only          # Bump version without pushing
    uv run python publish.py --no-bump            # Skip version bump, just tag and push current version
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Literal

from termcolor import colored


def main() -> None:
    # Parse command line arguments to determine mode (test/prod/bump-only)
    args = parse_and_validate_arguments()

    # Read current version and calculate new bumped version
    current_version = get_current_version()
    print(colored(f"📦 Current version: {current_version}", "blue"))

    if args.no_bump:
        # Skip bumping, use current version
        new_version = current_version
        print(colored("⏭️  Skipping version bump", "yellow"))
    else:
        new_version = get_new_version(current_version, args.bump_type)
        print(colored(f"📦 New version: {new_version}", "blue"))

        # Ask user to confirm the version bump
        if confirm_version_bump(current_version, new_version) != "y":
            print(colored("❌ Aborted", "red"))
            sys.exit(0)

        # Update pyproject.toml with new version and sync dependencies
        update_version_and_sync(new_version)

        # Stage changes and create commit
        git_stage_and_commit(new_version)

    # Either just bump (manual push) or create tag and push
    if args.bump_only:
        print(colored("\n✅ Version bumped. Push manually with: git push", "green"))
    else:
        create_and_push_tag(new_version, target=args.target)


def parse_and_validate_arguments() -> argparse.Namespace:
    """Parse and validate command line arguments"""
    parser = argparse.ArgumentParser(description="Bump version and publish")
    parser.add_argument(
        "--target",
        type=str,
        choices=["testpypi", "pypi"],
        default="pypi",
        help="Publish target: 'testpypi' (dev- tag) or 'pypi' (v tag). Default is pypi",
    )
    parser.add_argument(
        "--bump-only",
        action="store_true",
        help="Only bump version, don't tag/push",
    )
    parser.add_argument(
        "--no-bump",
        action="store_true",
        help="Skip version bump, just tag and push current version",
    )
    parser.add_argument(
        "--bump-type",
        type=str,
        choices=["major", "minor", "patch"],
        default="patch",
        help="Type of version bump (major, minor, patch). Default is patch",
    )

    args = parser.parse_args()

    # Validate that --bump-only and --no-bump are not used together
    if args.bump_only and args.no_bump:
        parser.error("--bump-only and --no-bump cannot be used together")

    return args


def get_pyproject_path() -> Path:
    """Get the path to pyproject.toml"""
    return Path(__file__).resolve().parent / "pyproject.toml"


def get_current_version() -> str:
    """Read current version from pyproject.toml without bumping"""
    pyproject = get_pyproject_path()
    content = pyproject.read_text()
    match = re.search(r'version = "([^"]+)"', content)
    if not match:
        print(colored("❌ Could not find version in pyproject.toml", "red"))
        sys.exit(1)
    return match.group(1)


def get_new_version(current_version: str, bump_type: str = "patch") -> str:
    """
    Calculate new version based on current version and bump type.

    Args:
        current_version: Current semantic version string like "0.1.2"
        bump_type: Type of bump - "major", "minor", or "patch"

    Returns:
        New version string after bumping
    """
    # Validate version format (must be X.Y.Z)
    parts = current_version.split(".")
    if len(parts) != 3:
        print(
            colored(
                f"❌ Invalid version format: {current_version}. Expected X.Y.Z", "red"
            )
        )
        sys.exit(1)

    # Calculate new version based on bump type
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

    match bump_type:
        case "major":
            return f"{major + 1}.0.0"
        case "minor":
            return f"{major}.{minor + 1}.0"
        case _:  # patch
            return f"{major}.{minor}.{patch + 1}"


def confirm_version_bump(current: str, new: str) -> Literal["y", "n"]:
    """Ask user to confirm version bump. Loops until valid input is received."""
    while True:
        response = (
            input(
                colored(f"\n❓ Bump version from {current} to {new}? (y/n): ", "yellow")
            )
            .strip()
            .lower()
        )

        # Only accept 'y' or 'n', loop on invalid input
        if response in ("y", "n"):
            return response  # type: ignore
        else:
            print(colored("❌ Please enter 'y' or 'n'", "red"))


def run_command(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run shell command"""
    print(colored(f"▶ {cmd}", "cyan"))
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(colored(f"❌ Command failed: {result.stderr}", "red"))
        sys.exit(1)
    return result


def update_version_and_sync(new_version: str) -> None:
    """Update version in pyproject.toml"""
    # Replace version string in pyproject.toml
    pyproject = get_pyproject_path()
    content = pyproject.read_text()
    updated = re.sub(r'version = "[^"]+"', f'version = "{new_version}"', content)
    pyproject.write_text(updated)
    print(colored(f"✅ Updated version to {new_version}", "green"))

    # Sync dependencies to update uv.lock
    print(colored("\n🔄 Syncing dependencies...", "blue"))
    run_command("uv sync")


def git_stage_and_commit(new_version: str) -> None:
    """Check for changes and stage appropriate files"""
    # Check if there are any uncommitted changes
    print(colored("\n📋 Checking for uncommitted changes...", "blue"))
    status = run_command("git status --porcelain", check=False)

    # Parse the changed files from git status output
    changed_files = [
        line.split()[-1] for line in status.stdout.strip().split("\n") if line.strip()
    ]

    # If only pyproject.toml and uv.lock are changed, commit automatically
    if set(changed_files) == {"pyproject.toml", "uv.lock"}:
        run_command("git add pyproject.toml uv.lock")
        run_command(f'git commit -m "Bump version to {new_version}"')
        print(colored("✅ Committed version bump automatically", "green"))

    # If there are other changes, ask user what to do
    else:
        if changed_files:
            print(colored("\n⚠️  You have uncommitted changes:", "yellow"))
            print(status.stdout)
            commit_all = input(
                colored(
                    "\n❓ Include all changes in this version commit? (y/n): ",
                    "yellow",
                )
            )

            # Stage either all changes or just version files
            if commit_all.lower() == "y":
                run_command("git add -A")
                print(colored("✅ All changes will be included", "green"))
            else:
                run_command("git add pyproject.toml uv.lock")
                print(colored("✅ Only version files will be included", "green"))

            # Create commit with version bump message
            run_command(f'git commit -m "Bump version to {new_version}"')
        else:
            # No changes detected
            print(colored("No changes to commit", "yellow"))


def create_and_push_tag(new_version: str, target: str) -> None:
    """Create git tag and push to remote"""
    # Determine tag prefix and target based on test/prod mode
    is_test = target == "testpypi"
    tag = f"dev-{new_version}" if is_test else f"v{new_version}"
    target_name = "TestPyPI" if is_test else "PyPI"

    print(colored(f"\n🏷️  Creating tag: {tag} (will publish to {target_name})", "blue"))

    # Create tag, push commits, then push tag (triggers GitHub Actions)
    run_command(f"git tag {tag}")
    run_command("git push")
    run_command(f"git push origin {tag}")

    # Inform user about next steps
    print(
        colored(f"\n✅ Done! GitHub Actions will now publish to {target_name}", "green")
    )
    print(
        colored(
            "📊 Check progress: https://github.com/christianwhocodes/tawala/actions",
            "cyan",
        )
    )


if __name__ == "__main__":
    main()
