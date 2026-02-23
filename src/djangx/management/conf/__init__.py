"""Settings configuration."""

from pathlib import Path

from django.utils.csp import CSP  # pyright: ignore[reportMissingTypeStubs]

from ... import PACKAGE, PROJECT
from .appdef import *
from .auth import *
from .runcommands import *
from .security import *
from .server import *
from .startproject import *
from .tailwindcss import *

BASE_DIR: Path = PROJECT.base_dir

from .generate import *  # Placed last to Ensures GENERATED_ENV_FIELDS has all available env vars for generation of .env.example

ROOT_URLCONF: str = f"{PACKAGE.name}.management.urls"

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

# ==============================================================================
# Internationalization
# https://docs.djangoproject.com/en/stable/topics/i18n/
# ==============================================================================

LANGUAGE_CODE: str = "en-us"

TIME_ZONE: str = "Africa/Nairobi"

USE_I18N: bool = True

USE_TZ: bool = True
