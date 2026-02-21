"""Tailwind CSS settings."""

from pathlib import Path

from ... import PACKAGE, PROJECT
from .. import ConfField, ManagementConf

__all__: list[str] = [
    "TAILWIND",
    "TAILWIND_SOURCE_STATIC_URL",
    "TAILWIND_OUTPUT_STATIC_URL",
]


class _TailwindConf(ManagementConf):
    """Tailwind CSS settings."""

    _default_version = "v4.2.0"

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
        default=Path(f"~/.local/bin/tailwindcss-{_default_version}.exe").expanduser(),
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
    """Return the path portion after 'static/' as a forward-slash string."""
    for parent in file_path.parents:
        if parent.name == "static":
            return file_path.relative_to(parent).as_posix()
    return file_path.name


TAILWIND_SOURCE_STATIC_URL: str = _static_relative_path(TAILWIND.source)

TAILWIND_OUTPUT_STATIC_URL: str = _static_relative_path(TAILWIND.output)
