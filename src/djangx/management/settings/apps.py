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
from ..enums import Apps, ContextProcessors, Middlewares
from ..types import TemplatesDict

# TODO: Refactor so that the user can specify the order of apps, middleware, and context processors more flexibly.

# ===============================================================
# Apps
# ===============================================================


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
        Apps.HTTP_COMPRESSION,
        Apps.MINIFY_HTML,
        Apps.BROWSER_RELOAD,
        Apps.WATCHFILES,
    ]

    django_apps: list[str] = [
        Apps.ADMIN,
        Apps.AUTH,
        Apps.CONTENTTYPES,
        Apps.SESSIONS,
        Apps.MESSAGES,
        Apps.STATICFILES,
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


_APP_CONTEXT_PROCESSOR_MAP: dict[Apps, list[ContextProcessors]] = {
    Apps.AUTH: [ContextProcessors.AUTH],
    Apps.MESSAGES: [ContextProcessors.MESSAGES],
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
        ContextProcessors.DEBUG,  # Debug info (only in DEBUG mode)
        ContextProcessors.REQUEST,  # Adds request object to context
        ContextProcessors.AUTH,  # Adds user and perms to context
        ContextProcessors.MESSAGES,  # Adds messages to context
        ContextProcessors.CSP,  # Content Security Policy
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


_APP_MIDDLEWARE_MAP: dict[Apps, list[Middlewares]] = {
    Apps.SESSIONS: [Middlewares.SESSION],
    Apps.AUTH: [Middlewares.AUTH],
    Apps.MESSAGES: [Middlewares.MESSAGES],
    Apps.HTTP_COMPRESSION: [Middlewares.HTTP_COMPRESSION],
    Apps.MINIFY_HTML: [Middlewares.MINIFY_HTML],
    Apps.BROWSER_RELOAD: [Middlewares.BROWSER_RELOAD],
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
