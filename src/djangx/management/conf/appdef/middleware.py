"""Installed apps, middleware, and template settings."""

from ...enums import MiddlewareEnum
from .._base import BaseConf, ConfField
from ._mappings import APP_MIDDLEWARE_MAP
from .installed_apps import INSTALLED_APPS


class _MiddlewareConf(BaseConf):
    """Middleware settings."""

    extend = ConfField(
        type=list,
        env="MIDDLEWARE_EXTEND",
        toml="middleware.extend",
        default=[],
    )
    remove = ConfField(
        type=list,
        env="MIDDLEWARE_REMOVE",
        toml="middleware.remove",
        default=[],
    )


_MIDDLEWARE_CONF = _MiddlewareConf()


def _get_middleware(installed_apps: list[str]) -> list[str]:
    """Build the final MIDDLEWARE list based on installed apps."""
    base_middleware: list[str] = [
        MiddlewareEnum.SECURITY,  # FIRST - security headers, HTTPS redirect
        MiddlewareEnum.SESSION,  # Early - needed by auth & messages
        MiddlewareEnum.COMMON,  # Early - URL normalization
        MiddlewareEnum.CSRF,  # After session - needs session data
        MiddlewareEnum.AUTH,  # After session - stores user in session
        MiddlewareEnum.MESSAGES,  # After session & auth
        MiddlewareEnum.CLICKJACKING,  # Security headers (X-Frame-Options)
        MiddlewareEnum.CSP,  # Security headers (Content-Security-Policy)
        MiddlewareEnum.HTTP_COMPRESSION,  # Before minify - encodes responses (Zstandard, Brotli, Gzip)
        MiddlewareEnum.MINIFY_HTML,  # After compression, before HTML modifiers
        MiddlewareEnum.BROWSER_RELOAD,  # LAST - dev only, injects reload script into HTML
    ]

    # Collect middleware that should be removed based on missing apps
    middleware_to_remove: set[str] = set(_MIDDLEWARE_CONF.remove)
    for app, middleware_list in APP_MIDDLEWARE_MAP.items():
        if app not in installed_apps:
            middleware_to_remove.update(middleware_list)

    # Filter out middleware whose apps are not installed or explicitly removed
    base_middleware: list[str] = [m for m in base_middleware if m not in middleware_to_remove]

    # Add custom middleware at the end (before browser reload if it exists)
    all_middleware: list[str] = base_middleware + _MIDDLEWARE_CONF.extend

    # Remove duplicates while preserving order
    return list(dict.fromkeys(all_middleware))


MIDDLEWARE: list[str] = _get_middleware(INSTALLED_APPS)

__all__: list[str] = ["MIDDLEWARE"]
