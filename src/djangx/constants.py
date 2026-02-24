"""Package enumerations and constants."""

from enum import StrEnum
from pathlib import Path
from typing import Final, Literal

from christianwhocodes import Version


class Package:
    """Package metadata and paths as enum for easy access."""

    BASE_DIR: Final[Path] = Path(__file__).parent.resolve()
    CONTRIB_APPS_DIR: Final[Path] = BASE_DIR / "contrib"
    NAME: Final[Literal["djangx"]] = "djangx"
    DISPLAY_NAME: Final[Literal["DjangX"]] = "DjangX"
    SETTINGS_MODULE: Final[str] = f"{NAME}.management.settings"
    VERSION: Final[str] = Version.get(NAME)[0]


class Project:
    """Project-specific constants."""

    BASE_DIR: Final[Path] = Path.cwd()
    API_DIR: Final[Path] = BASE_DIR / "api"
    PUBLIC_DIR: Final[Path] = BASE_DIR / "public"
    HOME_APP_DIR: Final[Path] = BASE_DIR / "home"
    HOME_APP_NAME: Final[str] = HOME_APP_DIR.name


class InstalledApps(StrEnum):
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


class Middlewares(StrEnum):
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


class ContextProcessors(StrEnum):
    """Template context processors."""

    DEBUG = "django.template.context_processors.debug"
    REQUEST = "django.template.context_processors.request"
    AUTH = "django.contrib.auth.context_processors.auth"
    MESSAGES = "django.contrib.messages.context_processors.messages"
    CSP = "django.template.context_processors.csp"


class AppDefMappings:
    """App definition Mappings."""

    APP_CONTEXT_PROCESSOR: Final[dict[InstalledApps, list[ContextProcessors]]] = {
        InstalledApps.AUTH: [ContextProcessors.AUTH],
        InstalledApps.MESSAGES: [ContextProcessors.MESSAGES],
    }

    APP_MIDDLEWARE: Final[dict[InstalledApps, list[Middlewares]]] = {
        InstalledApps.SESSIONS: [Middlewares.SESSION],
        InstalledApps.AUTH: [Middlewares.AUTH],
        InstalledApps.MESSAGES: [Middlewares.MESSAGES],
        InstalledApps.HTTP_COMPRESSION: [Middlewares.HTTP_COMPRESSION],
        InstalledApps.MINIFY_HTML: [Middlewares.MINIFY_HTML],
        InstalledApps.BROWSER_RELOAD: [Middlewares.BROWSER_RELOAD],
    }


class FileGenerateChoices(StrEnum):
    """Available file generation options."""

    DOTENV_EXAMPLE = ".env.example"
    API_SERVER_PY = "api/server.py"
    VERCEL_JSON = "vercel.json"
    PG_SERVICE = "pg_service"
    PGPASS = "pgpass"


class DatabaseChoices(StrEnum):
    """Available database backends."""

    SQLITE3 = "sqlite3"
    POSTGRESQL = "postgresql"


class PostgresFlags(StrEnum):
    """Flag to indicate whether to use environment variables for PostgreSQL configuration."""

    USE_ENV_VARS = "--pg-use-env-vars"


class StorageChoices(StrEnum):
    """Available storage backends."""

    FILESYSTEM = "filesystem"
    VERCELBLOB = "vercelblob"


class PresetChoices(StrEnum):
    """Available project presets."""

    DEFAULT = "default"
    VERCEL = "vercel"
