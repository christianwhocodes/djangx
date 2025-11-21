"""
Django settings.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

from pathlib import Path

from decouple import Csv, config
from django.core.management.utils import get_random_secret_key

# from django.utils.csp import CSP

# ==============================================================================
# Directories
# Build paths inside the project like this: BASE_DIR / 'subdir'.
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
RESOURCES_DIR = BASE_DIR / "resources"


# ==============================================================================
# Security
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/
# ! SECURITY WARNING: keep the SECRET_KEY used in production secret.
# ! SECURITY WARNING: don't run with DEBUG turned on in production.
# ! SECURITY WARNING: be intentional about ALLOWED_HOSTS - the specific domains/IPs allowed to run the app on.
# ==============================================================================

SECRET_KEY = get_random_secret_key()
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())

# SSL/HTTPS Security
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
    "djangx.ui",
    "djangx.utils",
    "app",
]

if DEBUG:
    INSTALLED_APPS += [
        "django_browser_reload",
        "django_watchfiles",
    ]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # "django.middleware.csp.ContentSecurityPolicyMiddleware",
]

if DEBUG:
    MIDDLEWARE += [
        "django_browser_reload.middleware.BrowserReloadMiddleware",
    ]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # "django.template.context_processors.csp",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# ==============================================================================
# Database
# https://docs.djangoproject.com/en/dev/ref/databases/#postgresql-notes
# https://www.postgresql.org/docs/current/libpq-pgservice.html
# https://www.postgresql.org/docs/current/libpq-pgpass.html
# ==============================================================================

DB_BACKEND = config("DB_BACKEND", default="sqlite3")

match DB_BACKEND:
    case "sqlite3" | "sqlite":
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": RESOURCES_DIR / "db.sqlite3",
            }
        }
    case "postgresql" | "postgres":
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "OPTIONS": {
                    "pool": True,
                    "service": config("PG_SERVICE", default=""),
                },
            }
        }
    case _:
        raise ValueError(f"Unsupported DB_BACKEND: {DB_BACKEND}")


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
# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/
# ==============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True


# ==============================================================================
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/
# ==============================================================================

STATIC_URL = f"/{RESOURCES_DIR.name}/static/"
STATIC_ROOT = RESOURCES_DIR / "static"


# ==============================================================================
# Media files (User-uploaded content)
# https://docs.djangoproject.com/en/dev/ref/settings/#media-files
# ==============================================================================

MEDIA_URL = f"/{RESOURCES_DIR.name}/media/"
MEDIA_ROOT = RESOURCES_DIR / "media"


# ==============================================================================
# Default primary key field type
# https://docs.djangoproject.com/en/dev/ref/settings/#default-auto-field
# ==============================================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ==============================================================================
# Content Security Policy (CSP)
# https://docs.djangoproject.com/en/dev/howto/csp/
# ==============================================================================

# SECURE_CSP = {
#     "default-src": [CSP.SELF],
#     "script-src": [CSP.SELF, CSP.NONCE],
#     # Example of the less secure 'unsafe-inline' option.
#     # "style-src": [CSP.SELF, CSP.UNSAFE_INLINE],
# }
