from pathlib import Path
from typing import TypedDict

from .conf import Conf, ConfField
from .pkg import PKG
from .project import PROJECT


class TailwindConf(Conf):
    """Tailwind configuration settings."""

    version = ConfField(env="TAILWIND_VERSION", toml="tailwind.version", type=str)
    cli = ConfField(env="TAILWIND_CLI", toml="tailwind.cli", type=Path)


class TailwindDict(TypedDict):
    """Type definition for Tailwind configuration dictionary."""

    version: str
    cli: Path
    source: Path
    output: Path


_tailwind = TailwindConf()


def _get_tailwind_config() -> TailwindDict:
    """Generate Tailwind configuration."""

    version: str = _tailwind.version or "v4.1.18"
    cli_path: Path = _tailwind.cli or Path(f"~/.local/bin/tailwind-{version}.exe").expanduser()

    return {
        "version": version,
        "cli": cli_path,
        "source": PROJECT["dirs"]["APP"] / "static" / "app" / "global.css",
        "output": PKG["dir"] / "static" / PKG["name"] / "global" / "output.css",
    }


TAILWIND: TailwindDict = _get_tailwind_config()
__all__ = ["TAILWIND"]
