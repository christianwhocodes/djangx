"""Pre app initialization

The PKG and PROJECT variables are used to configure the following files which are loaded before app and settings initialization:

- manage.py
- conf/config.py
- core/api/[a|w]sgi.py
- components/[ui|utils]/apps.py

* Do not use them in any other file

Note the order:
- pre.py configures config.py, which in turns is used to configure settings.py.
- We are using config.py to easily manage fetching of settings from either .env or pyproject.toml in the user's project directory
- settings.py is then loaded by Django, from which, in post.py, we centralize the variables that are used within ui and utils..
"""

from pathlib import Path
from typing import Any, Literal, NoReturn, Optional

from christianwhocodes.exceptions import DirectoryNotFoundError
from christianwhocodes.helpers import ExitCode, version_placeholder


class _Package:
    name: Literal["tawala"] = "tawala"  # all lower case
    dir: Path = Path(__file__).resolve().parent.parent.parent

    @staticmethod
    def get_version(package: str = name) -> str:
        from importlib.metadata import version

        try:
            return version(package)
        except Exception:
            return version_placeholder()


class _Project:
    """Directory path configuration and validation of project structure."""

    _cached_base_dir: Optional[Path] = None
    _cached_is_valid: Optional[bool] = None
    _cached_toml_section: Optional[dict[str, Any]] = None

    @classmethod
    def _detect_base_dir(cls) -> tuple[Path, bool, Optional[dict[str, Any]]]:
        """Detect if we're in a valid project and cache the results."""

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
                    return cwd, False, None
        else:
            return cwd, False, None

    @classmethod
    def _get_base_dir_on_initial_load(cls) -> Path:
        """
        Get the Tawala app base directory or raise ProjectError.

        Returns:
            Path: The base directory of the Tawala app.

        Raises:
            ProjectError: If not in a valid Tawala app base directory.
        """
        if cls._cached_base_dir is None:
            cls._cached_base_dir, cls._cached_is_valid, cls._cached_toml_section = (
                cls._detect_base_dir()
            )

        if not cls._cached_is_valid:
            raise DirectoryNotFoundError(
                "Are you currently executing in a Tawala app base directory? "
                "If not navigate to your app's root or "
                "create a new Tawala app to run the command.",
                expected_dir="A Tawala app root directory",
            )

        return cls._cached_base_dir

    @classmethod
    def get_base_dir_or_exit(cls) -> Path | NoReturn:
        """Get the Tawala app base directory or exit with an error."""
        try:
            return cls._get_base_dir_on_initial_load()
        except DirectoryNotFoundError as e:
            import sys

            print(str(e))
            sys.exit(ExitCode.ERROR)

    @classmethod
    def get_base_dir(cls) -> Path:
        """
        Returns:
            Path: The base directory.
        """
        if cls._cached_is_valid and cls._cached_base_dir is not None:
            return cls._cached_base_dir
        else:
            return cls.get_base_dir_or_exit()

    @classmethod
    def get_toml_section(cls) -> dict[str, Any]:
        """
        * Only use when the pyproject.toml [tool.tawala] section has already been validated.

        Returns:
            dict[str, Any]: The [tool.tawala] section in pyproject.toml.
        """
        assert cls._cached_toml_section is not None, (
            "Only use when the pyproject.toml [tool.tawala] section has already been validated."
        )
        return cls._cached_toml_section


PKG = _Package()
PROJECT = _Project()

__all__ = ["PKG", "PROJECT"]
