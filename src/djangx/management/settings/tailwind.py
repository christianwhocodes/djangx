from pathlib import Path

from ... import PKG_UI_DIR, PKG_UI_NAME, PROJECT_MAIN_APP_DIR, PROJECT_MAIN_APP_NAME, Conf, ConfField


class TailwindConf(Conf):
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
        default=PROJECT_MAIN_APP_DIR / "static" / PROJECT_MAIN_APP_NAME / "css" / "tailwind.css",
    )
    output = ConfField(
        type=Path,
        default=PKG_UI_DIR / "static" / PKG_UI_NAME / "css" / "tailwind.min.css",
    )


TAILWIND = TailwindConf()


__all__: list[str] = ["TAILWIND"]
