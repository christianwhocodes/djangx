#!/usr/bin/env python3
"""
Streamlined script to bump version, tag, and push to git.

Usage:
    uv run python publish.py            # Bump patch, tag vX.X.X, push to GitHub
    uv run python publish.py --pypi     # Bump patch, tag release-X.X.X, triggers PyPI Action
    uv run python publish.py --bump-only # Bump locally only
    uv run python publish.py --no-bump  # Tag/Push current version
"""

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from rich.console import Console
from rich.prompt import Confirm, Prompt

console = Console()


@dataclass
class PublishConfig:
    pypi: bool
    bump_only: bool
    no_bump: bool
    bump_type: Literal["major", "minor", "patch"]
    commit_message: str | None

    @property
    def tag_prefix(self) -> str:
        return "release-" if self.pypi else "v"

    @property
    def target_name(self) -> str:
        return "PyPI" if self.pypi else "GitHub"


class VersionManager:
    def __init__(self, pyproject_path: Path):
        self.path = pyproject_path

    def get_current_version(self) -> str:
        content = self.path.read_text()
        # Anchored regex to prevent matching dependencies
        match = re.search(r'^version = "([^"]+)"', content, re.MULTILINE)
        if not match:
            console.print("❌ Could not find 'version' in pyproject.toml", style="red")
            sys.exit(1)
        return match.group(1)

    def calculate_new_version(self, current: str, bump_type: str) -> str:
        try:
            major, minor, patch = map(int, current.split("."))
        except ValueError:
            console.print(
                f"❌ Invalid version format: {current}. Expected X.Y.Z", style="red"
            )
            sys.exit(1)

        match bump_type:
            case "major":
                return f"{major + 1}.0.0"
            case "minor":
                return f"{major}.{minor + 1}.0"
            case _:
                return f"{major}.{minor}.{patch + 1}"

    def update_version(self, new_version: str) -> None:
        content = self.path.read_text()
        updated = re.sub(
            r'^version = "[^"]+"',
            f'version = "{new_version}"',
            content,
            flags=re.MULTILINE,
        )
        self.path.write_text(updated)
        console.print(f"✅ Updated pyproject.toml to {new_version}", style="green")


class GitManager:
    def run(
        self, cmd: list[str] | str, check: bool = True
    ) -> subprocess.CompletedProcess:
        """Unified command runner."""
        if isinstance(cmd, str):
            # Simple string command (shell=True for pipes/simple syntax)
            console.print(f"▶ {cmd}", style="cyan", highlight=False)
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        else:
            # List command (safer, no shell)
            console.print(f"▶ {' '.join(cmd)}", style="cyan", highlight=False)
            result = subprocess.run(cmd, capture_output=True, text=True)

        if check and result.returncode != 0:
            console.print(f"❌ Command failed:\n{result.stderr}", style="red")
            sys.exit(1)
        return result

    def get_status(self) -> list[str]:
        res = self.run(["git", "status", "--porcelain"], check=False)
        return [line.split()[-1] for line in res.stdout.splitlines() if line.strip()]

    def commit_changes(self, new_version: str, msg_detail: str | None) -> None:
        console.print("\n📋 Checking for uncommitted changes...", style="blue")
        changed_files = self.get_status()

        if not changed_files:
            console.print("No changes to commit", style="yellow")
            return

        files_to_add = ["pyproject.toml", "uv.lock"]
        only_version_files = set(changed_files).issubset(set(files_to_add))

        if only_version_files:
            self.run(["git", "add"] + files_to_add)
        else:
            console.print("\n⚠️  Uncommitted changes found:", style="yellow")
            for f in changed_files:
                console.print(f"  - {f}")

            if Confirm.ask(
                "\n❓ Include ALL changes in this commit? (n = only version files)"
            ):
                self.run(["git", "add", "-A"])
            else:
                self.run(["git", "add"] + files_to_add)

        full_msg = f"Bump version to {new_version}"
        if msg_detail:
            full_msg += f"\n\n{msg_detail}"

        self.run(["git", "commit", "-m", full_msg])

    def push_tag(self, version: str, config: PublishConfig) -> None:
        tag = f"{config.tag_prefix}{version}"
        console.print(
            f"\n🏷️  Tagging {tag} (Target: {config.target_name})...", style="blue"
        )

        self.run(["git", "tag", tag])
        self.run(["git", "push"])
        self.run(["git", "push", "origin", tag])

        if config.pypi:
            console.print("\n🚀 Triggered PyPI publish action!", style="green")
            console.print(
                "📊 Check: https://github.com/christianwhocodes/tawala/actions",
                style="link cyan",
            )
        else:
            console.print("\n✅ Pushed tag to GitHub.", style="green")


def parse_args() -> PublishConfig:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Changed from --target to --pypi boolean
    parser.add_argument(
        "--pypi", action="store_true", help="Use 'release-' tag to trigger PyPI publish"
    )

    parser.add_argument(
        "--bump-only", action="store_true", help="Bump version locally, no push"
    )
    parser.add_argument(
        "--no-bump", action="store_true", help="Skip bump, push current"
    )
    parser.add_argument(
        "--bump-type",
        choices=["major", "minor", "patch"],
        default="patch",
        help="Bump type",
    )
    parser.add_argument("-m", "--message", help="Commit message details")

    args = parser.parse_args()
    if args.bump_only and args.no_bump:
        parser.error("Cannot use --bump-only and --no-bump together")

    return PublishConfig(
        pypi=args.pypi,
        bump_only=args.bump_only,
        no_bump=args.no_bump,
        bump_type=args.bump_type,
        commit_message=args.message,
    )


def main():
    cfg = parse_args()
    vm = VersionManager(Path(__file__).parent / "pyproject.toml")
    gm = GitManager()

    current_ver = vm.get_current_version()
    console.print(f"📦 Current: [bold]{current_ver}[/]")

    new_ver = current_ver
    if not cfg.no_bump:
        new_ver = vm.calculate_new_version(current_ver, cfg.bump_type)

        if not Confirm.ask(
            f"\n❓ Bump to [bold green]{new_ver}[/] ({cfg.target_name} tag)?"
        ):
            console.print("❌ Aborted", style="red")
            sys.exit(0)

        additional_msg = cfg.commit_message
        if additional_msg is None:
            additional_msg = (
                Prompt.ask("\n💬 Extra commit message (optional)", default="") or None
            )

        vm.update_version(new_ver)
        console.print("\n🔄 Syncing uv...", style="blue")
        gm.run("uv sync")
        gm.commit_changes(new_ver, additional_msg)
    else:
        console.print("⏭️  Skipping version bump", style="yellow")

    if not cfg.bump_only:
        gm.push_tag(new_ver, cfg)
    else:
        console.print("\n✅ Local bump complete. (Push skipped)", style="green")


if __name__ == "__main__":
    main()
