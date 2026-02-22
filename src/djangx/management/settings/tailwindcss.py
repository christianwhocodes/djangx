"""TailwindCSS settings."""

from pathlib import Path

from ... import PACKAGE, PROJECT
from .. import ConfField, ManagementConf

__all__: list[str] = [
    "TAILWINDCSS",
    "TAILWINDCSS_SOURCE_STATIC_URL",
    "TAILWINDCSS_OUTPUT_STATIC_URL",
]


class _TailwindCSSConf(ManagementConf):
    """TailwindCSS settings."""

    _default_version = "v4.2.0"

    version = ConfField(
        type=str,
        env="TAILWINDCSS_VERSION",
        toml="tailwindcss.version",
        default=_default_version,
    )
    cli = ConfField(
        type=Path,
        env="TAILWINDCSS_CLI",
        toml="tailwindcss.cli",
        default=Path(f"~/.local/bin/tailwindcss-{_default_version}.exe").expanduser(),
    )
    source = ConfField(
        type=Path,
        default=PROJECT.home_app_dir / "static" / PROJECT.home_app_name / "css" / "source.css",
    )
    output = ConfField(
        type=Path,
        default=PACKAGE.main_app_dir / "static" / PACKAGE.main_app_name / "css" / "output.css",
    )
    disable = ConfField(
        type=bool,
        env="TAILWINDCSS_DISABLE",
        toml="tailwindcss.disable",
        default=False,
    )
    no_watch = ConfField(
        type=bool,
        env="TAILWINDCSS_NO_WATCH",
        toml="tailwindcss.no_watch",
        default=False,
    )


TAILWINDCSS = _TailwindCSSConf()


def _static_relative_path(file_path: Path) -> str:
    """Return the path portion after 'static/' as a forward-slash string."""
    for parent in file_path.parents:
        if parent.name == "static":
            return file_path.relative_to(parent).as_posix()
    return file_path.name


TAILWINDCSS_SOURCE_STATIC_URL: str = _static_relative_path(TAILWINDCSS.source)

TAILWINDCSS_OUTPUT_STATIC_URL: str = _static_relative_path(TAILWINDCSS.output)
