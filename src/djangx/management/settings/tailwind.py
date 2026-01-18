from pathlib import Path

from ... import PKG_PATH, Conf, ConfField


class TailwindConf(Conf):
    """Tailwind configuration settings."""

    _default_version = "v4.1.18"

    version = ConfField(
        env="TAILWIND_VERSION",
        toml="tailwind.version",
        default=_default_version,
        type=str,
    )
    cli = ConfField(
        env="TAILWIND_CLI",
        toml="tailwind.cli",
        default=Path(f"~/.local/bin/tailwind-{_default_version}.exe").expanduser(),
        type=Path,
    )
    source = ConfField(
        default=Path.cwd() / "home" / "static" / "home" / "css" / "tailwind.css",
        type=Path,
    )
    output = ConfField(
        default=PKG_PATH / "ui" / "static" / "ui" / "css" / "tailwind.min.css",
        type=Path,
    )


TAILWIND = TailwindConf()


__all__: list[str] = ["TAILWIND"]
