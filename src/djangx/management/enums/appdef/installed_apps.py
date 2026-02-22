"""Installed Apps enums."""

from enum import StrEnum


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


__all__: list[str] = ["AppEnum"]
