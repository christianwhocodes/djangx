"""App definitions enums."""

from enum import StrEnum

from ... import PACKAGE

__all__: list[str] = ["AppEnum", "MiddlewareEnum", "TemplateContextProcessorEnum"]


class AppEnum(StrEnum):
    """Installed applications."""

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


class MiddlewareEnum(StrEnum):
    """Middleware classes in recommended order."""

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


class TemplateContextProcessorEnum(StrEnum):
    """Template context processors."""

    DEBUG = "django.template.context_processors.debug"
    REQUEST = "django.template.context_processors.request"
    AUTH = "django.contrib.auth.context_processors.auth"
    MESSAGES = "django.contrib.messages.context_processors.messages"
    CSP = "django.template.context_processors.csp"
    TAILWINDCSS = f"{PACKAGE.name}.management.context_processors.tailwindcss"
