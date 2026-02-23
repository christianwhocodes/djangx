"""API backend (ASGI/WSGI)."""

from os import environ

from .... import PACKAGE
from ...conf import SERVER_USE_ASGI

environ.setdefault("DJANGO_SETTINGS_MODULE", PACKAGE.settings_module)

__all__: list[str] = ["SERVER_APPLICATION"]


if SERVER_USE_ASGI:
    from .asgi import SERVER_APPLICATION
else:
    from .wsgi import SERVER_APPLICATION
