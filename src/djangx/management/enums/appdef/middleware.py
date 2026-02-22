"""Middleware enums."""

from enum import StrEnum


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


__all__: list[str] = ["MiddlewareEnum"]
