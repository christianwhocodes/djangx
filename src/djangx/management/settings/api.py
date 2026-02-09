"""API server settings configuration."""

from ... import PACKAGE
from .config import ConfField, SettingConfig

__all__: list[str] = [
    "SERVER_USE_ASGI",
    "ASGI_APPLICATION",
    "WSGI_APPLICATION",
]


class _ServerConf(SettingConfig):
    """Server application configuration settings (ASGI/WSGI)."""

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
