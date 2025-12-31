from typing import Any, Literal

from django.utils.csp import CSP  # type: ignore[reportMissingTypeStubs]

from .commands import *  # noqa: F403
from .contact import *  # noqa: F403
from .databases import *  # noqa: F403
from .email import *  # noqa: F403
from .org import *  # noqa: F403
from .pkg import *  # noqa: F403
from .project import *  # noqa: F403
from .security import *  # noqa: F403
from .social_media import *  # noqa: F403
from .storages import *  # noqa: F403
from .tailwind import *  # noqa: F403
from .urls import *  # noqa: F403

# ==============================================================================
# Application definition
# ==============================================================================

INSTALLED_APPS: list[str] = [
    PKG["name"],  # noqa: F405
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

ROOT_URLCONF: str = f"{PKG['name']}.urls"  # noqa: F405
WSGI_APPLICATION: str = f"{PKG['name']}.api.wsgi.application"  # noqa: F405


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
# Internationalization
# https://docs.djangoproject.com/en/stable/topics/i18n/
# ==============================================================================

LANGUAGE_CODE: str = "en-us"
TIME_ZONE: str = "Africa/Nairobi"
USE_I18N: bool = True
USE_TZ: bool = True


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
