"""API backend (ASGI/WSGI)."""

from os import environ

from .... import PACKAGE
from ...settings import SERVER_USE_ASGI

__all__: list[str] = ["SERVER_APPLICATION"]

environ.setdefault("DJANGO_SETTINGS_MODULE", PACKAGE.settings_module)

if SERVER_USE_ASGI:
    from .asgi import SERVER_APPLICATION
else:
    from .wsgi import SERVER_APPLICATION
