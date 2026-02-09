"""Initialization."""

import sys
from dataclasses import dataclass
from enum import StrEnum
from os import environ
from pathlib import Path
from typing import Any, ClassVar, Final

from christianwhocodes import ExitCode, Text, print

__all__: list[str] = [
    "PACKAGE",
    "PROJECT",
]


class _SkippedArgsEnum(StrEnum):
    STARTPROJECT = "startproject"
    INIT = "init"
    NEW = "new"


_SKIP_ARGS: Final[set[_SkippedArgsEnum]] = {
    _SkippedArgsEnum.STARTPROJECT,
    _SkippedArgsEnum.INIT,
    _SkippedArgsEnum.NEW,
}


# ============================================================================
# Package & Project Configuration
# ============================================================================


@dataclass(frozen=True)
class _PackageInfo:
    """Package configuration."""

    version: Final[str]
    """The package version, retrieved from metadata."""

    base_dir: Final[Path]
    """The root directory of the package."""

    main_app_dir: Final[Path]
    """Path to the `app` application directory."""

    name: Final[str]
    """The package name (derived from base_dir)."""

    display_name: Final[str]
    """Human-readable display name for the package."""

    main_app_name: Final[str]
    """Name of the `app` application."""

    settings_module: Final[str]
    """Django Settings Module"""

    @classmethod
    def create(cls) -> "_PackageInfo":
        """Create _PackageInfo with default package values.

        Returns:
            _PackageInfo instance configured for the current package.

        """
        from christianwhocodes import Version

        base_dir = Path(__file__).parent.resolve()
        name = base_dir.name
        main_app_dir = base_dir / "app"
        return cls(
            version=Version.get(name)[0],
            base_dir=base_dir,
            main_app_dir=main_app_dir,
            name=name,  # djangx
            display_name=name[0].upper() + name[1:-1] + name[-1].upper(),  # DjangX
            main_app_name=main_app_dir.name,  # app
            settings_module=f"{name}.management.settings",
        )


PACKAGE = _PackageInfo.create()
"""Package configuration instance."""


class _ProjectInfo:
    _toml_section: ClassVar[dict[str, Any] | None] = None
    _is_validated: ClassVar[bool] = False
    _base_dir: ClassVar[Path] = Path.cwd()

    @classmethod
    def _should_skip_validation(cls) -> bool:
        """Check if the current command should skip project validation."""
        return len(sys.argv) > 1 and sys.argv[1] in _SKIP_ARGS

    def __init__(self):
        """Initialize and validate project on first instantiation."""
        if not self._is_validated and not self._should_skip_validation():
            self._load_project()

        self.base_dir: Final[Path] = self._base_dir
        self.init_name: Final[str] = self.base_dir.name
        self.home_app_dir: Final[Path] = self.base_dir / "home"
        self.home_app_exists: Final[bool] = self.home_app_dir.exists() and self.home_app_dir.is_dir()
        self.home_app_name: Final[str] = self.home_app_dir.name
        self.public_dir: Final[Path] = self.base_dir / "public"
        self.api_dir: Final[Path] = self.base_dir / "api"

    @classmethod
    def _check_pyproject_toml(cls) -> dict[str, Any]:
        f"""
        Validate and extract 'tool.{PACKAGE.name}' configuration from 'pyproject.toml'.

        Returns:
            The 'tool.{PACKAGE.name}' configuration section from 'pyproject.toml'

        Raises:
            FileNotFoundError: If 'pyproject.toml' doesn't exist
            KeyError: If 'tool.{PACKAGE.name}' section is missing
        """
        from christianwhocodes import PyProject

        pyproject_path = cls._base_dir / "pyproject.toml"

        if not pyproject_path.exists():
            raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

        tool_section = PyProject(pyproject_path).data.get("tool", {})

        if PACKAGE.name in tool_section:
            return tool_section[PACKAGE.name]
        else:
            raise KeyError(f"Missing 'tool.{PACKAGE.name}' section in pyproject.toml")

    @classmethod
    def _load_project(cls) -> None:
        """Load and validate project configuration.

        Attempts to read and validate the pyproject.toml file. On success, stores
        the TOML configuration section. On failure, prints diagnostic messages
        and exits with an error code.
        """
        try:
            toml_section = cls._check_pyproject_toml()

        except (FileNotFoundError, KeyError, ValueError) as e:
            cls._is_validated = False
            print(f"Not in a valid {PACKAGE.display_name} project directory.", Text.ERROR)
            print(
                f"A valid project requires: pyproject.toml with a 'tool.{PACKAGE.name}' section (even if empty)",
                Text.INFO,
            )
            print(
                [
                    ("Create a new project: ", None),
                    (f"uvx {PACKAGE.name} startproject (if uv is installed.)", Text.HIGHLIGHT),
                ]
            )
            print(f"Validation error: {e}")

        except Exception as e:
            cls._is_validated = False
            print(
                f"Unexpected error during project validation:\n{e}",
                Text.WARNING,
            )

        else:
            # Success - store configuration
            cls._is_validated = True
            cls._toml_section = toml_section

        finally:
            if not cls._is_validated:
                sys.exit(ExitCode.ERROR)

    @property
    def env(self) -> dict[str, Any]:
        """Get combined .env and environment variables as a dictionary."""
        from dotenv import dotenv_values

        if not self._is_validated:
            if self._should_skip_validation():
                return dict(environ)
            self._load_project()
        return {
            **dotenv_values(self.base_dir / ".env"),
            **environ,  # override loaded values with environment variables
        }

    @property
    def toml(self) -> dict[str, Any]:
        """Get TOML configuration section."""
        if not self._is_validated:
            if self._should_skip_validation():
                return {}
            self._load_project()
        assert self._toml_section is not None
        return self._toml_section


PROJECT = _ProjectInfo()
"""Project configuration instance based on current working directory."""

# ============================================================================
# CLI
# ============================================================================


def main() -> None:
    """Execute the CLI.

    Routes commands to appropriate handlers using pattern matching.
    Falls back to Management utility for standard commands.

    Command routing:
    - version/-v/--version: Display package version
    - startproject/init/new: Initialize new project
    - *: Delegate to Management utility commands (runserver, migrate, etc.)
    """
    if len(sys.argv) < 2:
        print("No arguments passed.", Text.ERROR)
        sys.exit(ExitCode.ERROR)

    match sys.argv[1]:
        # ====================================================================
        # Version Display
        # ====================================================================
        case "-v" | "--version" | "version":
            from christianwhocodes import print_version

            sys.exit(print_version(PACKAGE.name))

        # ====================================================================
        # Project Initialization
        # ====================================================================
        case _SkippedArgsEnum.STARTPROJECT | _SkippedArgsEnum.INIT | _SkippedArgsEnum.NEW:
            from .management.commands import handle_startproject

            sys.exit(handle_startproject())

        # ====================================================================
        # Management Utility Commands (Fallback)
        # ====================================================================
        # All other commands are passed to Management utility
        # Examples: runserver, migrate, makemigrations, shell, etc.
        case _:
            from django.core.management import ManagementUtility

            # Add project directory to Python path for imports
            sys.path.insert(0, str(PROJECT.base_dir))

            # Set default settings module
            environ.setdefault("DJANGO_SETTINGS_MODULE", PACKAGE.settings_module)

            # Create and execute Management utility
            utility = ManagementUtility(sys.argv)
            utility.prog_name = PACKAGE.name
            utility.execute()


if __name__ == "__main__":
    main()
