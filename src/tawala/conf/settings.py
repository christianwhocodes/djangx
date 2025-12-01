from importlib.metadata import version
from typing import Any

from django.utils.csp import CSP  # type: ignore[reportMissingTypeStubs]

from .management import config, path


class Tawala:
    """Main configuration class that orchestrates settings."""

    def __init__(self):
        cached_base_dir = path.BasePath.get_cached_base_dir()

        if cached_base_dir is not None:
            # Already checked by CLI - reuse the cached value
            self.base_dir = cached_base_dir
        else:
            # Not yet checked (ASGI/WSGI context) - check now or exit
            self.base_dir = path.BasePath.get_base_dir_or_exit()

        self.version: str = version("tawala")
        self.security = config.SecurityConfig()
        self.apps = config.ApplicationConfig()
        self.db = config.DatabaseConfig()
        self.storage = config.StorageConfig()
        self.build = config.BuildConfig()


T = Tawala()

TAWALA_VERSION = T.version

# ==============================================================================
# Directories
# ==============================================================================

BASE_DIR = T.base_dir
assert BASE_DIR is not None, "BASE_DIR should have already been validated and cached."

API_DIR = BASE_DIR / "api"
APP_DIR = BASE_DIR / "app"
PUBLIC_DIR = BASE_DIR / "public"


# ==============================================================================
# Security & deployment checklist
# See https://docs.djangoproject.com/en/stable/howto/deployment/checklist/
# ==============================================================================

SECRET_KEY = T.security.secret_key
DEBUG = T.security.debug
ALLOWED_HOSTS = T.security.allowed_hosts

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # SECURE_HSTS_SECONDS = 3600


# ==============================================================================
# Application definition
# ==============================================================================

ROOT_URLCONF = "tawala.conf.urls"
ASGI_APPLICATION = "tawala.conf.asgi.application"
WSGI_APPLICATION = "tawala.conf.wsgi.application"

INSTALLED_APPS: list[str] = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_browser_reload",
    "django_watchfiles",
    "tawala.components",
    "tawala.core",
    *T.apps.configured_apps,
    "app",
]

MIDDLEWARE = [
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

BUILD = {"commands": T.build.commands}


# ==============================================================================
# Database
# https://docs.djangoproject.com/en/dev/ref/databases/#postgresql-notes
# https://www.postgresql.org/docs/current/libpq-pgservice.html
# https://www.postgresql.org/docs/current/libpq-pgpass.html
# ==============================================================================

DBCONF = {
    "USER": T.db.user,
    "PASSWORD": T.db.password,
    "NAME": T.db.name,
    "HOST": T.db.host,
    "PORT": T.db.port,
}

db_config: dict[str, dict[str, Any]]

match T.db.backend:
    case "sqlite" | "sqlite3":  # Default
        db_config = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }
    case "postgresql" | "postgres" | "psql" | "pgsql" | "pg" | "psycopg":
        PG_SERVICE = {"service": T.db.service}
        db_config = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                **(DBCONF if T.db.use_vars else {}),
                "OPTIONS": {
                    **(PG_SERVICE if not T.db.use_vars else {}),
                    "pool": T.db.pool,
                    "sslmode": T.db.ssl_mode,
                },
            }
        }
    case _:
        raise ValueError(f"Unsupported DB backend: {T.db.backend}")

DATABASES = db_config

# ==============================================================================
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/
# ==============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = PUBLIC_DIR / "static"
STATICFILES_BACKEND = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    }
}


# ==============================================================================
# Storage & Media files (User-uploaded content)
# https://docs.djangoproject.com/en/dev/ref/settings/#storages
# https://docs.djangoproject.com/en/dev/ref/settings/#media-files
# ==============================================================================

match T.storage.backend:
    case "filesystem" | "local" | "fs":  # Default
        storage_config = {
            "default": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
            },
            **STATICFILES_BACKEND,
        }
        MEDIA_URL = "/media/"
        MEDIA_ROOT = PUBLIC_DIR / "media"
    case "vercel" | "vercelblob" | "vercel_blob" | "vercel-blob":
        storage_config = {
            "default": {
                "BACKEND": "tawala.core.backends.storage.VercelBlobStorage",
            },
            **STATICFILES_BACKEND,
        }
    case _:
        raise ValueError(f"Unsupported storage backend: {T.storage.backend}")

STORAGES = storage_config
STORAGE_TOKEN = T.storage.token


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

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# ==============================================================================
# Content Security Policy (CSP)
# https://docs.djangoproject.com/en/dev/howto/csp/
# ==============================================================================

SECURE_CSP = {
    "default-src": [CSP.SELF],
    "script-src": [CSP.SELF, CSP.NONCE],
    # Example of the less secure 'unsafe-inline' option.
    # "style-src": [CSP.SELF, CSP.UNSAFE_INLINE],
}
