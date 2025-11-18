#!/usr/bin/env python3
"""
Simple script to bump version, tag, and push to git.
Usage:
    uv run python publish.py                      # Bump version, tag as vX.X.X, push to GitHub (default)
    uv run python publish.py --target pypi        # Bump version, tag as release-X.X.X, push, publish to PyPI via GitHub Actions
    uv run python publish.py --bump-only          # Bump version without pushing
    uv run python publish.py --no-bump            # Skip version bump, just tag and push current version
    uv run python publish.py --bump-type minor    # Bump minor version instead of patch
"""


# TODO:
# This is my usual workflow when dealing with this -
# I do 'python publish.py --bump-only' first to bump version and update uv.lock
# Then I review the changes 'git commit --amend' to add more details in the commint message under the 'Bump version to [version]' commit message
# The I do 'python publish.py --no-bump' to tag and push to GitHub, and 'python publish.py --no-bump --target pypi' as well.
# ?: What should be improved here is to allow adding more details to the commit message so that I don't need to first necessarily do '--bump-only' (though I can if I want) if I want to straight up publish?
# Maybe prompt the user to enter additional commit message details after confirming the version bump.

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from rich.console import Console

console = Console()


@dataclass
class PublishConfig:
    """Configuration for the publish operation"""

    target: Literal["github", "pypi"]
    bump_only: bool
    no_bump: bool
    bump_type: Literal["major", "minor", "patch"]
    commit_message: str | None

    @property
    def should_bump(self) -> bool:
        """Whether we should bump the version"""
        return not self.no_bump

    @property
    def should_push(self) -> bool:
        """Whether we should push to remote"""
        return not self.bump_only

    @property
    def tag_prefix(self) -> str:
        """Get the appropriate tag prefix"""
        return "release-" if self.target == "pypi" else "v"

    @property
    def target_name(self) -> str:
        """Human-readable target name"""
        return "PyPI" if self.target == "pypi" else "GitHub"


class VersionManager:
    """Handles version reading and bumping"""

    def __init__(self, pyproject_path: Path):
        self.pyproject_path = pyproject_path

    def get_current_version(self) -> str:
        """Read current version from pyproject.toml"""
        content = self.pyproject_path.read_text()
        match = re.search(r'version = "([^"]+)"', content)
        if not match:
            console.print("❌ Could not find version in pyproject.toml", style="red")
            sys.exit(1)
        return match.group(1)

    def calculate_new_version(
        self, current_version: str, bump_type: Literal["major", "minor", "patch"]
    ) -> str:
        """Calculate new version based on current version and bump type"""
        parts = current_version.split(".")
        if len(parts) != 3:
            console.print(
                f"❌ Invalid version format: {current_version}. Expected X.Y.Z",
                style="red",
            )
            sys.exit(1)

        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

        match bump_type:
            case "major":
                return f"{major + 1}.0.0"
            case "minor":
                return f"{major}.{minor + 1}.0"
            case _:  # patch
                return f"{major}.{minor}.{patch + 1}"

    def update_version(self, new_version: str) -> None:
        """Update version in pyproject.toml"""
        content = self.pyproject_path.read_text()
        updated = re.sub(r'version = "[^"]+"', f'version = "{new_version}"', content)
        self.pyproject_path.write_text(updated)
        console.print(f"✅ Updated version to {new_version}", style="green")


class GitManager:
    """Handles git operations"""

    @staticmethod
    def run_command(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
        """Run shell command"""
        console.print(f"▶ {cmd}", style="cyan")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if check and result.returncode != 0:
            console.print(f"❌ Command failed: {result.stderr}", style="red")
            sys.exit(1)
        return result

    def sync_dependencies(self) -> None:
        """Sync dependencies to update uv.lock"""
        console.print("\n🔄 Syncing dependencies...", style="blue")
        self.run_command("uv sync")

    def commit_changes(
        self, new_version: str, additional_message: str | None = None
    ) -> None:
        """Stage and commit changes"""
        console.print("\n📋 Checking for uncommitted changes...", style="blue")
        status_result = self.run_command("git status --porcelain", check=False)
        status_output = status_result.stdout.strip()

        if not status_output:
            console.print("No changes to commit", style="yellow")
            return

        # Parse changed files from the status output
        changed_files = [
            line.split()[-1] for line in status_output.split("\n") if line.strip()
        ]

        # If only version files changed, commit automatically
        if set(changed_files) == {"pyproject.toml", "uv.lock"}:
            self.run_command("git add pyproject.toml uv.lock")
        else:
            # Ask user about other changes
            console.print("\n⚠️  You have uncommitted changes:", style="yellow")
            print(status_output)
            console.print(
                "\n❓ Include all changes in this version commit? (y/n): ",
                style="yellow",
                end="",
            )
            commit_all = input().strip().lower()

            if commit_all == "y":
                self.run_command("git add -A")
                console.print("✅ All changes will be included", style="green")
            else:
                self.run_command("git add pyproject.toml uv.lock")
                console.print("✅ Only version files will be included", style="green")

        # Build commit message
        commit_msg = f"Bump version to {new_version}"
        if additional_message:
            commit_msg += f"\n\n{additional_message}"

        # Escape quotes in the commit message
        commit_msg_escaped = commit_msg.replace('"', '\\"')
        self.run_command(f'git commit -m "{commit_msg_escaped}"')
        console.print("✅ Committed version bump", style="green")

    def create_and_push_tag(self, version: str, config: PublishConfig) -> None:
        """Create git tag and push to remote"""
        tag = f"{config.tag_prefix}{version}"

        console.print(
            f"\n🏷️  Creating tag: {tag} (target: {config.target_name})", style="blue"
        )

        self.run_command(f"git tag {tag}")
        self.run_command("git push")
        self.run_command(f"git push origin {tag}")

        if config.target == "pypi":
            console.print(
                f"\n✅ Done! GitHub Actions will now publish to {config.target_name}",
                style="green",
            )
            console.print(
                "📊 Check progress: https://github.com/christianwhocodes/tawala/actions",
                style="cyan",
            )
        else:
            console.print("\n✅ Done! Tagged and pushed to GitHub", style="green")


def parse_arguments() -> PublishConfig:
    """Parse and validate command line arguments"""
    parser = argparse.ArgumentParser(description="Bump version and publish")
    parser.add_argument(
        "-t",
        "--target",
        type=str,
        choices=["github", "pypi"],
        default="github",
        help="Publish target: 'github' (v tag, default) or 'pypi' (release- tag, triggers PyPI publish)",
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
    parser.add_argument(
        "-m",
        "--message",
        type=str,
        help="Additional commit message details",
    )

    args = parser.parse_args()

    if args.bump_only and args.no_bump:
        parser.error("--bump-only and --no-bump cannot be used together")

    return PublishConfig(
        target=args.target,
        bump_only=args.bump_only,
        no_bump=args.no_bump,
        bump_type=args.bump_type,
        commit_message=args.message,
    )


def confirm_version_bump(current: str, new: str) -> bool:
    """Ask user to confirm version bump"""
    while True:
        console.print(
            f"\n❓ Bump version from {current} to {new}? (y/n): ",
            style="yellow",
            end="",
        )
        response = input().strip().lower()

        if response in ("y", "n"):
            return response == "y"
        else:
            console.print("❌ Please enter 'y' or 'n'", style="red")


def prompt_for_commit_message() -> str | None:
    """Prompt user for additional commit message details"""
    console.print(
        "\n💬 Add additional commit message details? (Enter for none, or type message): ",
        style="yellow",
        end="",
    )
    message = input().strip()
    return message if message else None


def main() -> None:
    # Parse configuration
    config = parse_arguments()

    # Initialize managers
    pyproject_path = Path(__file__).resolve().parent / "pyproject.toml"
    version_manager = VersionManager(pyproject_path)
    git_manager = GitManager()

    # Get current version
    current_version = version_manager.get_current_version()
    console.print(f"📦 Current version: {current_version}", style="blue")

    # Determine version to use
    if config.should_bump:
        new_version = version_manager.calculate_new_version(
            current_version, config.bump_type
        )
        console.print(f"📦 New version: {new_version}", style="blue")

        # Confirm bump
        if not confirm_version_bump(current_version, new_version):
            console.print("❌ Aborted", style="red")
            sys.exit(0)

        # Get additional commit message if not provided via CLI
        additional_message = config.commit_message
        if additional_message is None:
            additional_message = prompt_for_commit_message()

        # Update version and sync dependencies
        version_manager.update_version(new_version)
        git_manager.sync_dependencies()
        git_manager.commit_changes(new_version, additional_message)
    else:
        new_version = current_version
        console.print("⏭️  Skipping version bump", style="yellow")

    # Push or just bump locally
    if config.should_push:
        git_manager.create_and_push_tag(new_version, config)
    else:
        console.print(
            "\n✅ Version bumped. Push manually with: git push", style="green"
        )


if __name__ == "__main__":
    main()
