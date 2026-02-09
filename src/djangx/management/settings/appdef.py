"""Django apps and middleware settings configuration."""

from typing import Final

from ... import PACKAGE, PROJECT
from ..enums import AppEnum, ContextProcessorEnum, MiddlewareEnum
from ..types import TemplatesDict
from .config import ConfField, SettingConf

# TODO: Refactor so that the user can specify the order of apps, middleware, and context processors more flexibly.

__all__: list[str] = [
    "INSTALLED_APPS",
    "ROOT_URLCONF",
    "MIDDLEWARE",
    "TEMPLATES",
]

# ============================================================================
# Configuration Classes
# ============================================================================


class _AppsConf(SettingConf):
    """Installed applications configuration settings."""

    extend = ConfField(
        type=list,
        env="APPS_EXTEND",
        toml="apps.extend",
        default=[],
    )
    remove = ConfField(
        type=list,
        env="APPS_REMOVE",
        toml="apps.remove",
        default=[],
    )


class _MiddlewareConf(SettingConf):
    """Middleware configuration settings."""

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


class _ContextProcessorsConf(SettingConf):
    """Template context processors configuration settings."""

    extend = ConfField(
        type=list,
        env="CONTEXT_PROCESSORS_EXTEND",
        toml="context-processors.extend",
        default=[],
    )
    remove = ConfField(
        type=list,
        env="CONTEXT_PROCESSORS_REMOVE",
        toml="context-processors.remove",
        default=[],
    )


_APPS_CONF = _AppsConf()
_MIDDLEWARE_CONF = _MiddlewareConf()
_CONTEXT_PROCESSORS_CONF = _ContextProcessorsConf()

# ============================================================================
# App-to-Middleware/ContextProcessor Dependency Maps
# ============================================================================

_APP_CONTEXT_PROCESSOR_MAP: Final[dict[AppEnum, list[ContextProcessorEnum]]] = {
    AppEnum.AUTH: [ContextProcessorEnum.AUTH],
    AppEnum.MESSAGES: [ContextProcessorEnum.MESSAGES],
}

_APP_MIDDLEWARE_MAP: Final[dict[AppEnum, list[MiddlewareEnum]]] = {
    AppEnum.SESSIONS: [MiddlewareEnum.SESSION],
    AppEnum.AUTH: [MiddlewareEnum.AUTH],
    AppEnum.MESSAGES: [MiddlewareEnum.MESSAGES],
    AppEnum.HTTP_COMPRESSION: [MiddlewareEnum.HTTP_COMPRESSION],
    AppEnum.MINIFY_HTML: [MiddlewareEnum.MINIFY_HTML],
    AppEnum.BROWSER_RELOAD: [MiddlewareEnum.BROWSER_RELOAD],
}

# ============================================================================
# Builder Functions
# ============================================================================


def _get_installed_apps() -> list[str]:
    """Build the final list of installed applications.

    Order: Local apps → Third-party apps → contrib apps
    This ensures local apps can override templates/static files from third-party and contrib apps.
    """
    base_apps: list[str] = [
        PROJECT.home_app_name,
        PACKAGE.name,
        f"{PACKAGE.name}.{PACKAGE.main_app_name}",
    ]

    third_party_apps: list[str] = [
        AppEnum.HTTP_COMPRESSION,
        AppEnum.MINIFY_HTML,
        AppEnum.BROWSER_RELOAD,
        AppEnum.WATCHFILES,
    ]

    contrib_apps: list[str] = [
        AppEnum.ADMIN,
        AppEnum.AUTH,
        AppEnum.CONTENTTYPES,
        AppEnum.SESSIONS,
        AppEnum.MESSAGES,
        AppEnum.STATICFILES,
    ]

    # Collect apps that should be removed except for base apps
    apps_to_remove: list[str] = [app for app in _APPS_CONF.remove if app not in base_apps]

    # Remove apps that are in the remove list
    contrib_apps: list[str] = [app for app in contrib_apps if app not in apps_to_remove]
    third_party_apps: list[str] = [app for app in third_party_apps if app not in apps_to_remove]

    # Combine
    all_apps: list[str] = _APPS_CONF.extend + base_apps + third_party_apps + contrib_apps

    # Remove duplicates while preserving order
    return list(dict.fromkeys(all_apps))


def _get_middleware(installed_apps: list[str]) -> list[str]:
    """Build the final list of middleware based on installed apps.

    Critical ordering (request flows top→bottom, response flows bottom→top):
    1. SecurityMiddleware - MUST be first for HTTPS redirects and security headers
    2. SessionMiddleware - Early, needed by auth and messages
    3. CommonMiddleware - URL normalization
    4. CsrfViewMiddleware - After session (needs session data)
    5. AuthenticationMiddleware - After session (stores user in session)
    6. MessageMiddleware - After session and auth
    7. ClickjackingMiddleware - Security headers
    8. CSP Middleware - Content Security Policy headers
    9. HttpCompressionMiddleware - BEFORE MinifyHtml (encodes responses with gzip/brotli/zstandard)
    10. MinifyHtmlMiddleware - AFTER compression, BEFORE browser reload (modifies HTML content)
    11. BrowserReloadMiddleware - LAST (dev only, modifies HTML to inject reload script)

    Note: MinifyHtmlMiddleware must be:
    - BELOW any middleware that encodes responses (like HttpCompressionMiddleware)
    - ABOVE any middleware that modifies HTML (like BrowserReloadMiddleware)
    """
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
    for app, middleware_list in _APP_MIDDLEWARE_MAP.items():
        if app not in installed_apps:
            middleware_to_remove.update(middleware_list)

    # Filter out middleware whose apps are not installed or explicitly removed
    base_middleware: list[str] = [m for m in base_middleware if m not in middleware_to_remove]

    # Add custom middleware at the end (before browser reload if it exists)
    all_middleware: list[str] = base_middleware + _MIDDLEWARE_CONF.extend

    # Remove duplicates while preserving order
    return list(dict.fromkeys(all_middleware))


def _get_context_processors(installed_apps: list[str]) -> list[str]:
    """Build the final list of context processors based on installed apps.

    Order matters: Later processors can override variables from earlier ones.
    Standard order: debug → request → auth → messages → custom
    """
    # contrib context processors in recommended order
    contrib_context_processors: list[str] = [
        ContextProcessorEnum.DEBUG,  # Debug info (only in DEBUG mode)
        ContextProcessorEnum.REQUEST,  # Adds request object to context
        ContextProcessorEnum.AUTH,  # Adds user and perms to context
        ContextProcessorEnum.MESSAGES,  # Adds messages to context
        ContextProcessorEnum.CSP,  # Content Security Policy
    ]

    # Collect context processors that should be removed based on missing apps
    context_processors_to_remove: set[str] = set(_CONTEXT_PROCESSORS_CONF.remove)
    for app, processor_list in _APP_CONTEXT_PROCESSOR_MAP.items():
        if app not in installed_apps:
            context_processors_to_remove.update(processor_list)

    # Filter out context processors whose apps are not installed or explicitly removed
    contrib_context_processors: list[str] = [
        cp for cp in contrib_context_processors if cp not in context_processors_to_remove
    ]

    # Add custom context processors at the end
    all_context_processors: list[str] = _CONTEXT_PROCESSORS_CONF.extend + contrib_context_processors

    # Remove duplicates while preserving order
    return list(dict.fromkeys(all_context_processors))


# ============================================================================
# Django Settings
# ============================================================================

INSTALLED_APPS: list[str] = _get_installed_apps()

MIDDLEWARE: list[str] = _get_middleware(INSTALLED_APPS)

ROOT_URLCONF: str = f"{PACKAGE.name}.app.urls"

TEMPLATES: TemplatesDict = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": _get_context_processors(INSTALLED_APPS),
        },
    },
]
