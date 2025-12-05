from pathlib import Path
from typing import Any, Literal

from django.utils.csp import CSP  # type: ignore[reportMissingTypeStubs]

from .presettings import (
    CommandsConfig,
    DatabaseConfig,
    PackageConfig,
    ProjectConfig,
    SecurityConfig,
    StorageConfig,
    TailwindCLIConfig,
)


class Settings:
    """Main configuration class that orchestrates settings."""

    def __init__(self) -> None:
        self.package = PackageConfig()
        self.project = ProjectConfig()
        self.security = SecurityConfig()
        self.database = DatabaseConfig()
        self.storage = StorageConfig()
        self.tailwind_cli = TailwindCLIConfig()
        self.commands = CommandsConfig()


SETTINGS = Settings()

# ==============================================================================
# Package
# ==============================================================================

PKG_NAME = SETTINGS.package.name
PKG_DIR = SETTINGS.package.dir
PKG_VERSION = SETTINGS.package.version


# ==============================================================================
# Project
# ==============================================================================

BASE_DIR = SETTINGS.project.base_dir
APP_DIR = BASE_DIR / "app"
API_DIR = BASE_DIR / "api"
PUBLIC_DIR = BASE_DIR / "public"
CLI_DIR = BASE_DIR / ".cli"


# ==============================================================================
# Security & deployment checklist
# See https://docs.djangoproject.com/en/stable/howto/deployment/checklist/
# ==============================================================================

SECRET_KEY: str = SETTINGS.security.secret_key
DEBUG: bool = SETTINGS.security.debug
ALLOWED_HOSTS: list[str] = SETTINGS.security.allowed_hosts

# Production security settings
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # SECURE_HSTS_SECONDS = 3600


# ==============================================================================
# Application definition
# ==============================================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_browser_reload",
    "django_watchfiles",
    f"{PKG_NAME}.components.utils",
    f"{PKG_NAME}.components.ui",
    "app",
]

MIDDLEWARE: list[str] = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]

ROOT_URLCONF = f"{PKG_NAME}.core.app.urls"

TEMPLATES: list[dict[str, Any]] = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.csp",
            ],
        },
    },
]

WSGI_APPLICATION = f"{PKG_NAME}.core.api.wsgi.application"


# ==============================================================================
# Commands
# ==============================================================================

COMMANDS_INSTALL: list[str] = SETTINGS.commands.install

COMMANDS_BUILD: list[str] = SETTINGS.commands.build


# ==============================================================================
# Database Configuration
# https://docs.djangoproject.com/en/dev/ref/databases/#postgresql-notes
# https://www.postgresql.org/docs/current/libpq-pgservice.html
# https://www.postgresql.org/docs/current/libpq-pgpass.html
# ==============================================================================


def _get_database_config() -> dict[str, dict[str, Any]]:
    """Generate database configuration based on backend type."""
    backend = SETTINGS.database.backend.lower()

    match backend:
        case "postgresql" | "postgres" | "psql" | "pgsql" | "pg" | "psycopg":  # Default
            options: dict[str, Any] = {
                "pool": SETTINGS.database.pool,
                "sslmode": SETTINGS.database.ssl_mode,
            }

            # Add service or connection vars
            if SETTINGS.database.use_vars:
                config = {
                    "USER": SETTINGS.database.user,
                    "PASSWORD": SETTINGS.database.password,
                    "NAME": SETTINGS.database.name,
                    "HOST": SETTINGS.database.host,
                    "PORT": SETTINGS.database.port,
                }
            else:
                options["service"] = (
                    SETTINGS.database.service
                    if SETTINGS.database.service
                    else f"{PKG_NAME}-app"
                )
                config = {}

            return {
                "default": {
                    "ENGINE": "django.db.backends.postgresql",
                    "OPTIONS": options,
                    **config,
                }
            }

        case "sqlite" | "sqlite3":
            return {
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": BASE_DIR / "db.sqlite3",
                }
            }

        case _:
            raise ValueError(f"Unsupported DB backend: {backend}")


DATABASES = _get_database_config()


# ==============================================================================
# Tailwind CSS
# ==============================================================================

TAILWIND_CLI: dict[str, Any] = {
    "PATH": SETTINGS.tailwind_cli.path
    if SETTINGS.tailwind_cli.path
    else CLI_DIR / "tailwindcss" / "cli",
    "VERSION": SETTINGS.tailwind_cli.version,
    "CSS": {
        "input": APP_DIR / "static" / "app" / "css" / "input.css",
        "output": PKG_DIR
        / "components"
        / "ui"
        / "static"
        / "ui"
        / "css"
        / "output.css",
    },
}


# ==============================================================================
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/
# ==============================================================================

STATIC_URL = "/static/"
STATIC_ROOT: Path = PUBLIC_DIR / "static"


# ==============================================================================
# Storage & Media files (User-uploaded content)
# https://docs.djangoproject.com/en/dev/ref/settings/#storages
# https://docs.djangoproject.com/en/dev/ref/settings/#media-files
# ==============================================================================


def _get_storage_config() -> dict[str, Any]:
    """Generate storage configuration based on backend type."""
    backend = SETTINGS.storage.backend.lower()

    base_config: dict[str, dict[str, str] | str] = {
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        }
    }

    match backend:
        case "filesystem" | "local" | "fs":  # Default
            storage_backend = "django.core.files.storage.FileSystemStorage"
            global MEDIA_URL, MEDIA_ROOT
            MEDIA_URL = "/media/"
            MEDIA_ROOT = PUBLIC_DIR / "media"

        case "vercel" | "vercelblob" | "vercel_blob" | "vercel-blob":
            storage_backend = (
                f"{PKG_NAME}.components.utils.backends.storage.VercelBlobStorage"
            )

        case _:
            raise ValueError(f"Unsupported storage backend: {backend}")

    base_config["default"] = {"BACKEND": storage_backend}
    return base_config


STORAGES = _get_storage_config()
STORAGE_TOKEN = (SETTINGS.storage.token,)


# ==============================================================================
# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/
# ==============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True


# ==============================================================================
# Authentication & Password validation
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
# ==============================================================================

AUTH_PASSWORD_VALIDATORS: list[dict[Literal["NAME"], str]] = [
    {"NAME": f"django.contrib.auth.password_validation.{validator}"}
    for validator in [
        "UserAttributeSimilarityValidator",
        "MinimumLengthValidator",
        "CommonPasswordValidator",
        "NumericPasswordValidator",
    ]
]


# ==============================================================================
# Content Security Policy (CSP)
# https://docs.djangoproject.com/en/dev/howto/csp/
# ==============================================================================

SECURE_CSP: dict[str, list[str]] = {
    "default-src": [CSP.SELF],
    "script-src": [CSP.SELF, CSP.NONCE],
    # Example of the less secure 'unsafe-inline' option.
    # "style-src": [CSP.SELF, CSP.UNSAFE_INLINE],
}
