from pathlib import Path
from typing import Any, Optional


class NotBaseDirectoryError(Exception):
    """Raised when the current directory is not a Tawala app base directory."""

    pass


class BasePath:
    """Directory path configuration and validation of Tawala app project structure."""

    _cached_base_dir: Optional[Path] = None
    _cached_is_valid: Optional[bool] = None
    _cached_toml_section: Optional[dict[str, Any]] = None

    @classmethod
    def _detect_base_dir(cls) -> tuple[Optional[Path], bool, Optional[dict[str, Any]]]:
        """Detect if we're in a valid Tawala project and cache the results."""

        cwd = Path.cwd()
        pyproject_toml = cwd / "pyproject.toml"

        if pyproject_toml.exists() and pyproject_toml.is_file():
            import tomllib

            with pyproject_toml.open("rb") as f:
                toml_data = tomllib.load(f)

                # check for [tool.tawala] section
                toml_section: Optional[dict[str, Any]] = toml_data.get("tool", {}).get(
                    "tawala", None
                )
                if toml_section is not None:
                    return pyproject_toml.parent, True, toml_section
                else:
                    return None, False, None
        else:
            return None, False, None

    @classmethod
    def _get_base_dir(cls) -> Optional[Path]:
        """
        Get the Tawala app base directory or raise NotBaseDirectoryError.

        Returns:
            Path: The base directory of the Tawala app.

        Raises:
            NotBaseDirectoryError: If not in a valid Tawala app base directory.
        """
        if cls._cached_base_dir is None and cls._cached_is_valid is None:
            cls._cached_base_dir, cls._cached_is_valid, cls._cached_toml_section = (
                cls._detect_base_dir()
            )

        if not cls._cached_is_valid:
            raise NotBaseDirectoryError(
                "Not a Tawala app base directory. Navigate to your app's root or initialize a new Tawala app."
            )

        return cls._cached_base_dir

    @classmethod
    def get_base_dir_or_exit(cls) -> Optional[Path]:
        """Get the Tawala app base directory or exit with an error."""
        try:
            return cls._get_base_dir()
        except NotBaseDirectoryError as e:
            import sys

            from django.core.management.color import color_style

            print(color_style().ERROR(str(e)))
            sys.exit(1)

    @classmethod
    def get_cached_base_dir(cls) -> Optional[Path]:
        """
        Get the base directory if it has already been validated, otherwise return None.

        This is useful for contexts where validation has already happened
        and we want to reuse the cached result without re-checking.

        Returns:
            Optional[Path]: The cached base directory if already validated, None otherwise.
        """
        return cls._cached_base_dir if cls._cached_is_valid else None

    @classmethod
    def get_cached_toml_section(cls) -> Optional[dict[str, Any]]:
        """
        Get the pyproject.toml [tool.tawala] section if it has already been validated, otherwise return None.

        This is useful for contexts where validation has already happened
        and we want to reuse the cached result without re-checking.

        Returns:
            Optional[dict[str, Any]]: The cached [tool.tawala] section in pyproject.toml if already validated, None otherwise.
        """
        return cls._cached_toml_section if cls._cached_is_valid else None
