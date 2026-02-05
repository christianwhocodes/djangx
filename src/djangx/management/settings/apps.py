"""# DjangX settings: Installed apps, middleware, templates, context processors."""
# TODO: Refactor so that the user can specify the order of apps, middleware, and context processors more flexibly.

from enum import StrEnum

from ... import (
    INCLUDE_PROJECT_MAIN_APP,
    PKG_API_NAME,
    PKG_MANAGEMENT_NAME,
    PKG_NAME,
    PKG_UI_NAME,
    PROJECT_MAIN_APP_NAME,
    Conf,
    ConfField,
)
from ..types import TemplatesDict

# ===============================================================
# Apps
# ===============================================================


class _Apps(StrEnum):
    """Django applications enumeration."""

    ADMIN = "django.contrib.admin"
    AUTH = "django.contrib.auth"
    CONTENTTYPES = "django.contrib.contenttypes"
    SESSIONS = "django.contrib.sessions"
    MESSAGES = "django.contrib.messages"
    STATICFILES = "django.contrib.staticfiles"
    HTTP_COMPRESSION = "django_http_compression"
    MINIFY_HTML = "django_minify_html"
    BROWSER_RELOAD = "django_browser_reload"
    WATCHFILES = "django_watchfiles"


class AppsConf(Conf):
    """Apps configuration settings."""

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


_APPS_CONF = AppsConf()


def _get_installed_apps() -> list[str]:
    """Build the final list of installed Django applications.

    Order: Local apps → Third-party apps → Django apps
    This ensures local apps can override templates/static files from third-party and Django apps.
    """

    base_apps: list[str] = [
        *([PROJECT_MAIN_APP_NAME] if INCLUDE_PROJECT_MAIN_APP else []),
        PKG_NAME,
        f"{PKG_NAME}.{PKG_API_NAME}",
        f"{PKG_NAME}.{PKG_UI_NAME}",
    ]

    third_party_apps: list[str] = [
        _Apps.HTTP_COMPRESSION,
        _Apps.MINIFY_HTML,
        _Apps.BROWSER_RELOAD,
        _Apps.WATCHFILES,
    ]

    django_apps: list[str] = [
        _Apps.ADMIN,
        _Apps.AUTH,
        _Apps.CONTENTTYPES,
        _Apps.SESSIONS,
        _Apps.MESSAGES,
        _Apps.STATICFILES,
    ]

    # Collect apps that should be removed except for base apps
    apps_to_remove: list[str] = [app for app in _APPS_CONF.remove if app not in base_apps]

    # Remove apps that are in the remove list
    django_apps: list[str] = [app for app in django_apps if app not in apps_to_remove]
    third_party_apps: list[str] = [app for app in third_party_apps if app not in apps_to_remove]

    # Combine: local apps + third-party apps + django apps + custom extensions
    all_apps: list[str] = _APPS_CONF.extend + base_apps + third_party_apps + django_apps

    # Remove duplicates while preserving order
    return list(dict.fromkeys(all_apps))


INSTALLED_APPS: list[str] = _get_installed_apps()


# ===============================================================
# TEMPLATES & CONTEXT PROCESSORS
# ===============================================================


class _ContextProcessors(StrEnum):
    """Django template context processors enumeration."""

    DEBUG = "django.template.context_processors.debug"
    REQUEST = "django.template.context_processors.request"
    AUTH = "django.contrib.auth.context_processors.auth"
    MESSAGES = "django.contrib.messages.context_processors.messages"
    CSP = "django.template.context_processors.csp"


_APP_CONTEXT_PROCESSOR_MAP: dict[_Apps, list[_ContextProcessors]] = {
    _Apps.AUTH: [_ContextProcessors.AUTH],
    _Apps.MESSAGES: [_ContextProcessors.MESSAGES],
}


class ContextProcessorsConf(Conf):
    """Context processors configuration settings."""

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


_CONTEXT_PROCESSORS_CONF = ContextProcessorsConf()


def _get_context_processors(installed_apps: list[str]) -> list[str]:
    """Build the final list of context processors based on installed apps.

    Order matters: Later processors can override variables from earlier ones.
    Standard order: debug → request → auth → messages → custom
    """
    # Django context processors in recommended order
    django_context_processors: list[str] = [
        _ContextProcessors.DEBUG,  # Debug info (only in DEBUG mode)
        _ContextProcessors.REQUEST,  # Adds request object to context
        _ContextProcessors.AUTH,  # Adds user and perms to context
        _ContextProcessors.MESSAGES,  # Adds messages to context
        _ContextProcessors.CSP,  # Content Security Policy
    ]

    # Collect context processors that should be removed based on missing apps
    context_processors_to_remove: set[str] = set(_CONTEXT_PROCESSORS_CONF.remove)
    for app, processor_list in _APP_CONTEXT_PROCESSOR_MAP.items():
        if app not in installed_apps:
            context_processors_to_remove.update(processor_list)

    # Filter out context processors whose apps are not installed or explicitly removed
    django_context_processors: list[str] = [
        cp for cp in django_context_processors if cp not in context_processors_to_remove
    ]

    # Add custom context processors at the end
    all_context_processors: list[str] = _CONTEXT_PROCESSORS_CONF.extend + django_context_processors

    # Remove duplicates while preserving order
    return list(dict.fromkeys(all_context_processors))


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


# ===============================================================
# MIDDLEWARE
# ===============================================================


class _Middlewares(StrEnum):
    """Django middleware enumeration."""

    SECURITY = "django.middleware.security.SecurityMiddleware"
    SESSION = "django.contrib.sessions.middleware.SessionMiddleware"
    COMMON = "django.middleware.common.CommonMiddleware"
    CSRF = "django.middleware.csrf.CsrfViewMiddleware"
    AUTH = "django.contrib.auth.middleware.AuthenticationMiddleware"
    MESSAGES = "django.contrib.messages.middleware.MessageMiddleware"
    CLICKJACKING = "django.middleware.clickjacking.XFrameOptionsMiddleware"
    CSP = "django.middleware.csp.ContentSecurityPolicyMiddleware"
    HTTP_COMPRESSION = "django_http_compression.middleware.HttpCompressionMiddleware"
    MINIFY_HTML = "django_minify_html.middleware.MinifyHtmlMiddleware"
    BROWSER_RELOAD = "django_browser_reload.middleware.BrowserReloadMiddleware"


_APP_MIDDLEWARE_MAP: dict[_Apps, list[_Middlewares]] = {
    _Apps.SESSIONS: [_Middlewares.SESSION],
    _Apps.AUTH: [_Middlewares.AUTH],
    _Apps.MESSAGES: [_Middlewares.MESSAGES],
    _Apps.HTTP_COMPRESSION: [_Middlewares.HTTP_COMPRESSION],
    _Apps.MINIFY_HTML: [_Middlewares.MINIFY_HTML],
    _Apps.BROWSER_RELOAD: [_Middlewares.BROWSER_RELOAD],
}


class MiddlewareConf(Conf):
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


_MIDDLEWARE_CONF = MiddlewareConf()


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
    django_middleware: list[str] = [
        _Middlewares.SECURITY,  # FIRST - security headers, HTTPS redirect
        _Middlewares.SESSION,  # Early - needed by auth & messages
        _Middlewares.COMMON,  # Early - URL normalization
        _Middlewares.CSRF,  # After session - needs session data
        _Middlewares.AUTH,  # After session - stores user in session
        _Middlewares.MESSAGES,  # After session & auth
        _Middlewares.CLICKJACKING,  # Security headers (X-Frame-Options)
        _Middlewares.CSP,  # Security headers (Content-Security-Policy)
        _Middlewares.HTTP_COMPRESSION,  # Before minify - encodes responses (Zstandard, Brotli, Gzip)
        _Middlewares.MINIFY_HTML,  # After compression, before HTML modifiers
        _Middlewares.BROWSER_RELOAD,  # LAST - dev only, injects reload script into HTML
    ]

    # Collect middleware that should be removed based on missing apps
    middleware_to_remove: set[str] = set(_MIDDLEWARE_CONF.remove)
    for app, middleware_list in _APP_MIDDLEWARE_MAP.items():
        if app not in installed_apps:
            middleware_to_remove.update(middleware_list)

    # Filter out middleware whose apps are not installed or explicitly removed
    django_middleware: list[str] = [m for m in django_middleware if m not in middleware_to_remove]

    # Add custom middleware at the end (before browser reload if it exists)
    all_middleware: list[str] = django_middleware + _MIDDLEWARE_CONF.extend

    # Remove duplicates while preserving order
    return list(dict.fromkeys(all_middleware))


MIDDLEWARE: list[str] = _get_middleware(INSTALLED_APPS)


# ===============================================================
# ROOT URLCONF
# ===============================================================


ROOT_URLCONF: str = f"{PKG_NAME}.{PKG_MANAGEMENT_NAME}.urls"


# ===============================================================
# EXPORTS
# ===============================================================

__all__: list[str] = ["INSTALLED_APPS", "TEMPLATES", "MIDDLEWARE", "ROOT_URLCONF"]
