"""TailwindCSS settings."""

from pathlib import Path

from ... import PACKAGE, PROJECT
from ._conf import ConfField, ManagementConf

__all__: list[str] = [
    "TAILWINDCSS",
    "TAILWINDCSS_SOURCE_URL",
    "TAILWINDCSS_OUTPUT_URL",
]

# ============================================================================
# Configuration Classes
# ============================================================================


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
    is_disabled = ConfField(
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


# ============================================================================
# Helper Functions
# ============================================================================


def _static_path_to_url(file_path: Path) -> str:
    """Return the path portion after 'static/' as a forward-slash string.

    Example: /…/app/static/app/css/output.css -> "app/css/output.css"
    """
    for parent in file_path.parents:
        if parent.name == "static":
            return file_path.relative_to(parent).as_posix()
    return file_path.name


# ============================================================================
# Django Settings
# ============================================================================


TAILWINDCSS = _TailwindCSSConf()

TAILWINDCSS_SOURCE_URL: str = _static_path_to_url(TAILWINDCSS.source)

TAILWINDCSS_OUTPUT_URL: str = _static_path_to_url(TAILWINDCSS.output)
