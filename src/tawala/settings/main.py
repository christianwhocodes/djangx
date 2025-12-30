from pathlib import Path
from typing import Any, Literal

from django.utils.csp import CSP  # type: ignore[reportMissingTypeStubs]

from . import conf


class Settings:
    """Main configuration class that orchestrates settings."""

    def __init__(self) -> None:
        self.package = conf.PackageConf()
        self.project = conf.ProjectConf()
        self.security = conf.SecurityConf()
        self.app = conf.AppConf()
        self.database = conf.DatabaseConf()
        self.storage = conf.StorageConf()
        self.tailwindcss = conf.TailwindCSSConf()
        self.commands = conf.CommandsConf()


SETTINGS = Settings()

# ==============================================================================
# Package
# ==============================================================================

PKG_DIR: Path = SETTINGS.package.pkg_dir
PKG_NAME: str = SETTINGS.package.pkg_name
PKG_VERSION: str = SETTINGS.package.pkg_version


# ==============================================================================
# Project
# ==============================================================================

BASE_DIR: Path = SETTINGS.project.base_dir
APP_DIR: Path = SETTINGS.project.app_dir
API_DIR: Path = SETTINGS.project.api_dir
PUBLIC_DIR: Path = SETTINGS.project.public_dir


# ==============================================================================
# Security & deployment checklist
# See https://docs.djangoproject.com/en/stable/howto/deployment/checklist/
# ==============================================================================

SECRET_KEY: str = SETTINGS.security.secret_key or "django-insecure-change-me-in-production"
DEBUG: bool = SETTINGS.security.debug if SETTINGS.security.debug is not None else True
ALLOWED_HOSTS: list[str] = SETTINGS.security.allowed_hosts or ["localhost", "127.0.0.1"]

# Production security settings
if not DEBUG:
    SECURE_SSL_REDIRECT: bool = True
    SESSION_COOKIE_SECURE: bool = True
    CSRF_COOKIE_SECURE: bool = True
    # SECURE_HSTS_SECONDS = 3600


# ==============================================================================
# Application definition
# ==============================================================================

APP = {
    "NAME": SETTINGS.app.name or "Tawala",
    "SHORT_NAME": SETTINGS.app.short_name or "Tawala",
    "DESCRIPTION": SETTINGS.app.description or "Tawala Application",
}

INSTALLED_APPS: list[str] = [
    PKG_NAME,
    "app",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_browser_reload",
    "django_watchfiles",
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

ROOT_URLCONF: str = f"{PKG_NAME}.urls"

WSGI_APPLICATION: str = f"{PKG_NAME}.wsgi.application"


# ==============================================================================
# Templates
# ==============================================================================

TEMPLATES: list[dict[str, Any]] = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.csp",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ==============================================================================
# Database Configuration
# https://docs.djangoproject.com/en/stable/ref/databases/#postgresql-notes
# https://www.postgresql.org/docs/current/libpq-pgservice.html
# https://www.postgresql.org/docs/current/libpq-pgpass.html
# ==============================================================================


def _get_database_config() -> dict[str, dict[str, Any]]:
    """Generate database configuration based on backend type."""

    backend = SETTINGS.database.backend.lower() or "sqlite3"

    match backend:
        case "sqlite" | "sqlite3":
            return {
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": BASE_DIR / "db.sqlite3",
                }
            }
        case "postgresql" | "postgres" | "psql" | "pgsql" | "pg" | "psycopg":
            options: dict[str, Any] = {
                "pool": SETTINGS.database.pool if SETTINGS.database.pool is not None else False,
                "sslmode": SETTINGS.database.ssl_mode or "prefer",
            }

            # Add service or connection vars
            if (
                SETTINGS.database.use_vars if SETTINGS.database.use_vars is not None else False
            ) is True:
                config = {
                    "USER": SETTINGS.database.user,
                    "PASSWORD": SETTINGS.database.password,
                    "NAME": SETTINGS.database.name,
                    "HOST": SETTINGS.database.host,
                    "PORT": SETTINGS.database.port,
                }
            else:
                options["service"] = SETTINGS.database.service
                config = {}

            return {
                "default": {
                    "ENGINE": "django.db.backends.postgresql",
                    "OPTIONS": options,
                    **config,
                }
            }
        case _:
            raise ValueError(f"Unsupported DB backend: {backend}")


DATABASES: dict[str, dict[str, Any]] = _get_database_config()


# ==============================================================================
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/stable/howto/static-files/
# ==============================================================================

STATIC_URL: str = "/static/"
STATIC_ROOT: Path = PUBLIC_DIR / "static"


# ==============================================================================
# Storage & Media files (User-uploaded content)
# https://docs.djangoproject.com/en/stable/ref/settings/#storages
# https://docs.djangoproject.com/en/stable/ref/settings/#media-files
# ==============================================================================


def _get_storage_config() -> dict[str, Any]:
    """Generate storage configuration based on backend type."""

    backend = SETTINGS.storage.backend.lower() or "filesystem"

    base_config: dict[str, dict[str, str] | str] = {
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        }
    }

    match backend:
        case "filesystem" | "local" | "fs":
            storage_backend = "django.core.files.storage.FileSystemStorage"
            global MEDIA_URL, MEDIA_ROOT
            MEDIA_URL = "/media/"
            MEDIA_ROOT = PUBLIC_DIR / "media"

        case "vercel" | "vercelblob" | "vercel_blob" | "vercel-blob":
            storage_backend = f"{PKG_NAME}.backends.storage.VercelBlobStorage"

        case _:
            raise ValueError(f"Unsupported storage backend: {backend}")

    base_config["default"] = {"BACKEND": storage_backend}
    return base_config


STORAGES: dict[str, Any] = _get_storage_config()
STORAGE_TOKEN: str = SETTINGS.storage.token


# ==============================================================================
# TailwindCSS
# ==============================================================================


def _get_tailwindcss_config() -> dict[str, str | Path]:
    """Generate TailwindCSS configuration."""

    version = SETTINGS.tailwindcss.version or "v4.1.18"
    cli_path = (
        SETTINGS.tailwindcss.cli or Path(f"~/.local/bin/tailwindcss-{version}.exe").expanduser()
    )

    return {
        "VERSION": version,
        "CLI": cli_path,
        "SOURCE": APP_DIR / "static" / "app" / "css" / "source.css",
        "OUTPUT": PKG_DIR / "static" / "vendors" / "tailwindcss" / "output.css",
    }


TAILWINDCSS = _get_tailwindcss_config()


# ==============================================================================
# Commands
# ==============================================================================

COMMANDS: dict[str, list[str]] = {
    "INSTALL": SETTINGS.commands.install,
    "BUILD": SETTINGS.commands.build
    or [
        "makemigrations",
        "migrate",
        "tailwindcss build",
        "collectstatic --noinput",
    ],
}


# ==============================================================================
# Internationalization
# https://docs.djangoproject.com/en/stable/topics/i18n/
# ==============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True


# ==============================================================================
# Authentication & Password validation
# https://docs.djangoproject.com/en/stable/ref/settings/#auth-password-validators
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
# https://docs.djangoproject.com/en/stable/howto/csp/
# ==============================================================================

SECURE_CSP: dict[str, list[str]] = {
    "default-src": [CSP.SELF],
    "script-src": [CSP.SELF, CSP.NONCE],
    "style-src": [
        CSP.SELF,
        CSP.NONCE,
        "https://fonts.googleapis.com",  # Google Fonts CSS
    ],
    "font-src": [
        CSP.SELF,
        "https://fonts.gstatic.com",  # Google Fonts font files
    ],
}
