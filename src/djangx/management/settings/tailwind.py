"""Tailwind CSS settings configuration."""

from pathlib import Path

from ... import PACKAGE, PROJECT
from .config import ConfField, SettingConf

__all__: list[str] = [
    "TAILWIND",
    "TAILWIND_SOURCE_STATIC_URL",
    "TAILWIND_OUTPUT_STATIC_URL",
]


class _TailwindConf(SettingConf):
    """Tailwind configuration settings."""

    _default_version = "v4.1.18"

    version = ConfField(
        type=str,
        env="TAILWIND_VERSION",
        toml="tailwind.version",
        default=_default_version,
    )
    cli = ConfField(
        type=Path,
        env="TAILWIND_CLI",
        toml="tailwind.cli",
        default=Path(f"~/.local/bin/tailwind-{_default_version}.exe").expanduser(),
    )
    source = ConfField(
        type=Path,
        default=PROJECT.home_app_dir / "static" / PROJECT.home_app_name / "css" / "tailwind.css",
    )
    output = ConfField(
        type=Path,
        default=PACKAGE.main_app_dir / "static" / PACKAGE.main_app_name / "css" / "tailwind.min.css",
    )


TAILWIND = _TailwindConf()


def _static_relative_path(file_path: Path) -> str:
    """Return the portion after static/ as a forward-slash string.

    Given an absolute path under a ``static/`` directory, return the
    portion after ``static/`` as a forward-slash string suitable for
    Django's ``static()`` helper.

    Falls back to the bare filename when no ``static`` ancestor is found.
    """
    for parent in file_path.parents:
        if parent.name == "static":
            return file_path.relative_to(parent).as_posix()
    return file_path.name


TAILWIND_SOURCE_STATIC_URL: str = _static_relative_path(TAILWIND.source)

TAILWIND_OUTPUT_STATIC_URL: str = _static_relative_path(TAILWIND.output)
