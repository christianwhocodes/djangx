"""Initialization."""

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
    """Raised when the current directory is not a valid project."""


class _SkipArgsEnum(StrEnum):
    STARTPROJECT = "startproject"
    INIT = "init"
    NEW = "new"


# ============================================================================
# Package Configuration
# ============================================================================


@dataclass(frozen=True)
class _PackageInfo:
    """Package configuration (The toolkit itself)."""

    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.resolve())

    @property
    def name(self) -> str:
        """The package name (derived from base_dir) - djangx."""
        return self.base_dir.name

    @property
    def display_name(self) -> str:
        """Human-readable display name for the package - DjangX."""
        return f"{self.name[0].upper()}{self.name[1:-1]}{self.name[-1].upper()}"

    @cached_property
    def version(self) -> str:
        """The package version, retrieved lazily from metadata."""
        from christianwhocodes import Version

        return Version.get(self.name)[0]

    @property
    def main_app_dir(self) -> Path:
        """Path to the `app` application directory."""
        return self.base_dir / "app"

    @property
    def main_app_name(self) -> str:
        """Name of the `app` application."""
        return self.main_app_dir.name

    @property
    def settings_module(self) -> str:
        """Django Settings Module."""
        return f"{self.name}.management.settings"


PACKAGE: Final = _PackageInfo()


# ============================================================================
# Project Configuration
# ============================================================================


@dataclass(frozen=True)
class _ProjectInfo:
    """Project configuration based on current working directory."""

    base_dir: Path = field(default_factory=Path.cwd)
    # Track validation state via a list to allow mutation in a frozen dataclass
    _validated: list[bool] = field(default_factory=lambda: [False], init=False, repr=False)

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
        """Get TOML configuration section. Evaluated lazily and cached."""
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
        """Get combined .env and environment variables. Evaluated lazily."""
        self.validate()
        from dotenv import dotenv_values

        return {**dotenv_values(self.base_dir / ".env"), **environ}

    def validate(self) -> None:
        """Check if the current directory is a valid project.

        Triggers once. In CLI, we catch the exception for pretty printing.
        In Production, this will bubble up to the WSGI/ASGI server.
        """
        if self._validated[0]:
            return

        # Avoid validation during project creation commands
        skip_cmds = set(_SkipArgsEnum)
        if any(arg in sys.argv for arg in skip_cmds):
            self._validated[0] = True
            return

        try:
            _ = self.toml
        except (FileNotFoundError, KeyError) as e:
            raise ProjectValidationError(str(e)) from e

        self._validated[0] = True


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
                print(f"Unexpected error during project validation:\n{e}", Text.WARNING)
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
