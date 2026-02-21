"""Package initialization and CLI entry point."""

import sys
from dataclasses import dataclass, field
from enum import StrEnum
from functools import cached_property
from os import environ
from pathlib import Path
from typing import Any, Final

from christianwhocodes import ExitCode, Text, print

__all__: list[str] = [
    "PACKAGE",
    "PROJECT",
    "ProjectValidationError",
]


# ============================================================================
# Helpers
# ============================================================================


class ProjectValidationError(Exception):
    """Current directory is not a valid project."""


class _SkipArgsEnum(StrEnum):
    STARTPROJECT = "startproject"
    INIT = "init"
    NEW = "new"


# ============================================================================
# Package Configuration
# ============================================================================


@dataclass(frozen=True)
class _PackageInfo:
    """Package metadata and paths."""

    @property
    def name(self) -> str:
        """Package name."""
        return "djangx"

    @property
    def display_name(self) -> str:
        """Human-readable package name."""
        return "DjangX"

    @cached_property
    def version(self) -> str:
        """Package version (lazy-loaded)."""
        from christianwhocodes import Version

        return Version.get(self.name)[0]

    @property
    def main_app_dir(self) -> Path:
        """Path to the main app directory."""
        return Path(__file__).parent.resolve() / "app"

    @property
    def main_app_name(self) -> str:
        """Main app directory name."""
        return self.main_app_dir.name

    @property
    def settings_module(self) -> str:
        """Django settings module."""
        return f"{self.name}.management.settings"


PACKAGE: Final = _PackageInfo()


# ============================================================================
# Project Configuration
# ============================================================================


@dataclass(frozen=True)
class _ProjectInfo:
    """Project configuration for the current working directory."""

    base_dir: Path = field(default_factory=Path.cwd)
    # Internal flag to ensure validation runs only once. Kept private and not shown in repr.
    _validated: bool = field(default=False, init=False, repr=False)

    @property
    def init_name(self) -> str:
        return self.base_dir.name

    @property
    def home_app_dir(self) -> Path:
        return self.base_dir / "home"

    @property
    def home_app_exists(self) -> bool:
        return self.home_app_dir.exists() and self.home_app_dir.is_dir()

    @property
    def home_app_name(self) -> str:
        return self.home_app_dir.name

    @property
    def public_dir(self) -> Path:
        return self.base_dir / "public"

    @property
    def api_dir(self) -> Path:
        return self.base_dir / "api"

    @cached_property
    def toml(self) -> dict[str, Any]:
        """TOML configuration section (lazy-loaded, cached)."""
        from christianwhocodes import PyProject

        pyproject_path = self.base_dir / "pyproject.toml"

        if not pyproject_path.exists():
            raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

        tool_section = PyProject(pyproject_path).data.get("tool", {})
        if PACKAGE.name not in tool_section:
            raise KeyError(f"Missing 'tool.{PACKAGE.name}' section in pyproject.toml")

        return tool_section[PACKAGE.name]

    @cached_property
    def env(self) -> dict[str, Any]:
        """Combined .env and environment variables (lazy-loaded)."""
        self.validate()
        from dotenv import dotenv_values

        return {**dotenv_values(self.base_dir / ".env"), **environ}

    def validate(self) -> None:
        """Check if the current directory is a valid project. Runs once.

        In CLI, we catch the exception for pretty printing.
        In Production, this will bubble up to the WSGI/ASGI server.
        """
        if self._validated:
            return

        # Avoid validation during project creation commands
        skip_cmds = set(_SkipArgsEnum)
        if any(arg in sys.argv for arg in skip_cmds):
            object.__setattr__(self, "_validated", True)
            return

        try:
            _ = self.toml
        except (FileNotFoundError, KeyError) as e:
            raise ProjectValidationError(str(e)) from e

        object.__setattr__(self, "_validated", True)


PROJECT: Final = _ProjectInfo()


# ============================================================================
# CLI
# ============================================================================


def main() -> None:
    """Execute the CLI."""
    if len(sys.argv) < 2:
        print("No arguments passed.", Text.ERROR)
        sys.exit(ExitCode.ERROR)

    command = sys.argv[1]

    match command:
        case "-v" | "--version" | "version":
            from christianwhocodes import print_version

            sys.exit(print_version(PACKAGE.name))

        case _SkipArgsEnum.STARTPROJECT | _SkipArgsEnum.INIT | _SkipArgsEnum.NEW:
            from .management.commands import handle_startproject

            sys.exit(handle_startproject())

        case _:
            try:
                PROJECT.validate()
            except ProjectValidationError as e:
                print(f"Not in a valid {PACKAGE.display_name} project directory: {e}", Text.ERROR)
                sys.exit(ExitCode.ERROR)
            except Exception as e:
                print(f"Unexpected error during project validation:\n{e}", Text.ERROR)
                sys.exit(ExitCode.ERROR)
            else:
                from django.core.management import ManagementUtility

                sys.path.insert(0, str(PROJECT.base_dir))
                environ.setdefault("DJANGO_SETTINGS_MODULE", PACKAGE.settings_module)

                utility = ManagementUtility(sys.argv)
                utility.prog_name = PACKAGE.name
                utility.execute()


if __name__ == "__main__":
    main()
