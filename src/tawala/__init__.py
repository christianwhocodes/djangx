"""
Bootstrap configuration for tawala apps.

Exposes `PKG` and `PROJECT` for early initialization of:
- core/api/cli.py
- core/api/{a|w}sgi.py
- core/app/presettings.py
- components/u{i|tils}/apps.py

Import these symbols only during app bootstrap; avoid using them elsewhere.
"""

from pathlib import Path
from typing import Any, NoReturn, Optional

from christianwhocodes.helpers import ExitCode, PyProject, version_placeholder
from christianwhocodes.stdout import Text, print


class _Package:
    _file: Path = Path(__file__).resolve()

    def __init__(self) -> None:
        self.dir: Path = self._file.parent
        self.name: str = self.dir.stem

    @property
    def version(self) -> str:
        try:
            from importlib.metadata import version

            return version(self.name)
        except Exception:
            return version_placeholder()


PKG = _Package()


class _Project:
    """Directory path configuration and validation of project structure."""

    def __init__(self) -> None:
        self._base_dir: Optional[Path] = None
        self._toml_section: Optional[dict[str, Any]] = None
        self._valid_project: Optional[bool] = None

    @classmethod
    def _load_project(cls) -> Optional[NoReturn]:
        try:
            base_dir: Path = Path.cwd()
            toml_section: dict[str, Any] = PyProject(base_dir / "pyproject.toml").data[
                "tool"
            ][PKG.name]

        except (FileNotFoundError, KeyError):
            cls._valid_project = False
            print(
                f"Are you currently executing in a {PKG.name.capitalize()} app base directory? "
                f"If not navigate to your app's root or create a new {PKG.name.capitalize()} app to run the command.\n"
                f"'tool.{PKG.name}'section must be included in 'pyproject.toml' even if empty, "
                f"as it serves as a {PKG.name.capitalize()} app project identifier.",
                Text.WARNING,
            )

        except Exception as e:
            cls._valid_project = False
            print(str(e))

        else:
            cls._valid_project = True
            cls._base_dir = base_dir
            cls._toml_section = toml_section

        finally:
            if not cls._valid_project:
                from sys import exit

                exit(ExitCode.ERROR)

    @property
    def base_dir(self) -> Path:
        if not self._valid_project:
            self._load_project()

        assert self._base_dir is not None
        return self._base_dir

    @property
    def toml_section(self) -> dict[str, Any]:
        if not self._valid_project:
            self._load_project()

        assert self._toml_section is not None
        return self._toml_section


PROJECT = _Project()

__all__ = ["PKG", "PROJECT"]
