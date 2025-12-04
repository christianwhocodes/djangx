"""
Only use variables from conf/config.py, not from pre.py, to configure.

Note the order:
- pre.py configures config.py, which in turns is used to configure settings.py.
- We are using config.py to easily manage fetching of settings from either .env or pyproject.toml in the user's project directory
- settings.py is then loaded by Django, from which, in post.py, we centralize the variables that are used within ui and utils.
"""

from pathlib import Path
from typing import Any, Literal

from django.utils.csp import CSP  # type: ignore[reportMissingTypeStubs]

from . import config


class Settings:
    """Main configuration class that orchestrates settings."""

    def __init__(self):
        self.package = config.PackageConfig
        self.project = config.ProjectConfig
        self.security = config.SecurityConfig()
        self.apps = config.ApplicationConfig()
        self.database = config.DatabaseConfig()
        self.storage = config.StorageConfig()
        self.tailwind_cli = config.TailwindCLIConfig()
        self.commands = config.CommandsConfig()


T = Settings()

# ==============================================================================
# Package
# ==============================================================================

PKG_NAME = T.package.name
PKG_DIR = T.package.dir
PKG_VERSION = T.package.version


# ==============================================================================
# Project
# ==============================================================================

PROJECT_DIR = T.project.dir
BASE_DIR = PROJECT_DIR
APP_DIR = PROJECT_DIR / "app"
API_DIR = PROJECT_DIR / "api"
PUBLIC_DIR = PROJECT_DIR / "public"
CLI_DIR = PROJECT_DIR / ".cli"


# ==============================================================================
# Security & deployment checklist
# See https://docs.djangoproject.com/en/stable/howto/deployment/checklist/
# ==============================================================================

SECRET_KEY: str = T.security.secret_key
DEBUG: bool = T.security.debug
ALLOWED_HOSTS: list[str] = T.security.allowed_hosts

# Production security settings
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # SECURE_HSTS_SECONDS = 3600


# ==============================================================================
# Application definition
# ==============================================================================

ROOT_URLCONF = f"{PKG_NAME}.core.app.urls"

ASGI_APPLICATION = f"{PKG_NAME}.core.api.asgi.application"
WSGI_APPLICATION = f"{PKG_NAME}.core.api.wsgi.application"

INSTALLED_APPS: list[str] = [
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
    *T.apps.configured_apps,
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


# ==============================================================================
# Commands
# ==============================================================================

COMMANDS_INSTALL: list[str] = T.commands.install

COMMANDS_BUILD: list[str] = T.commands.build


# ==============================================================================
# Database Configuration
# https://docs.djangoproject.com/en/dev/ref/databases/#postgresql-notes
# https://www.postgresql.org/docs/current/libpq-pgservice.html
# https://www.postgresql.org/docs/current/libpq-pgpass.html
# ==============================================================================


def _get_database_config() -> dict[str, dict[str, Any]]:
    """Generate database configuration based on backend type."""
    backend = T.database.backend.lower()

    match backend:
        case "postgresql" | "postgres" | "psql" | "pgsql" | "pg" | "psycopg":  # Default
            options: dict[str, Any] = {
                "pool": T.database.pool,
                "sslmode": T.database.ssl_mode,
            }

            # Add service or connection vars
            if T.database.use_vars:
                config = {
                    "USER": T.database.user,
                    "PASSWORD": T.database.password,
                    "NAME": T.database.name,
                    "HOST": T.database.host,
                    "PORT": T.database.port,
                }
            else:
                options["service"] = (
                    T.database.service if T.database.service else f"{PKG_NAME}-app"
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
                    "NAME": PROJECT_DIR / "db.sqlite3",
                }
            }

        case _:
            raise ValueError(f"Unsupported DB backend: {backend}")


DATABASES = _get_database_config()


# ==============================================================================
# Tailwind CSS
# ==============================================================================

TAILWIND_CLI: dict[str, Any] = {
    "PATH": T.tailwind_cli.path if T.tailwind_cli.path else CLI_DIR / "tailwindcss",
    "VERSION": T.tailwind_cli.version,
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
    backend = T.storage.backend.lower()

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
STORAGE_TOKEN = (T.storage.token,)


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
