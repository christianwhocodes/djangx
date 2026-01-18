from ... import PKG_NAME, Conf, ConfField


class ServerConfig(Conf):
    """api configuration settings."""

    use_asgi = ConfField(env="SERVER_USE_ASGI", toml="server.use-asgi", type=bool, default=False)


_SERVER = ServerConfig()

SERVER_USE_ASGI: bool = _SERVER.use_asgi

ASGI_APPLICATION: str = f"{PKG_NAME}.api.backends.server.asgi.application"

WSGI_APPLICATION: str = f"{PKG_NAME}.api.backends.server.wsgi.application"


__all__: list[str] = ["SERVER_USE_ASGI", "ASGI_APPLICATION", "WSGI_APPLICATION"]
