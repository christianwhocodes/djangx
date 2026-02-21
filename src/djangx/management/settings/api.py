"""API server settings (ASGI/WSGI)."""

from ... import PACKAGE
from .config import ConfField, SettingConf

__all__: list[str] = [
    "SERVER_USE_ASGI",
    "ASGI_APPLICATION",
    "WSGI_APPLICATION",
]


class _ServerConf(SettingConf):
    """Server application settings."""

    use_asgi = ConfField(
        type=bool,
        env="SERVER_USE_ASGI",
        toml="server.use-asgi",
        default=False,
    )


_SERVER = _ServerConf()

SERVER_USE_ASGI: bool = _SERVER.use_asgi

ASGI_APPLICATION: str = f"{PACKAGE.name}.management.backends.api.asgi.SERVER_APPLICATION"

WSGI_APPLICATION: str = f"{PACKAGE.name}.management.backends.api.wsgi.SERVER_APPLICATION"
