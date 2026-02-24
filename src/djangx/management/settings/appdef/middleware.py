"""Installed apps, middleware, and template settings."""

from ....constants import AppDefMappings, Middlewares
from ...conf import BaseConf, ConfField
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
        Middlewares.SECURITY,  # FIRST - security headers, HTTPS redirect
        Middlewares.SESSION,  # Early - needed by auth & messages
        Middlewares.COMMON,  # Early - URL normalization
        Middlewares.CSRF,  # After session - needs session data
        Middlewares.AUTH,  # After session - stores user in session
        Middlewares.MESSAGES,  # After session & auth
        Middlewares.CLICKJACKING,  # Security headers (X-Frame-Options)
        Middlewares.CSP,  # Security headers (Content-Security-Policy)
        Middlewares.HTTP_COMPRESSION,  # Before minify - encodes responses (Zstandard, Brotli, Gzip)
        Middlewares.MINIFY_HTML,  # After compression, before HTML modifiers
        Middlewares.BROWSER_RELOAD,  # LAST - dev only, injects reload script into HTML
    ]

    # Collect middleware that should be removed based on missing apps
    middleware_to_remove: set[str] = set(_MIDDLEWARE_CONF.remove)
    for app, middleware_list in AppDefMappings.APP_MIDDLEWARE.items():
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
