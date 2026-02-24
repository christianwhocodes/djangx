"""Settings configuration."""

from pathlib import Path

from django.utils.csp import CSP  # pyright: ignore[reportMissingTypeStubs]

from ...constants import Package
from .appdef import *
from .auth import *
from .runcommands import *
from .security import *
from .server import *
from .startproject import *
from .tailwindcss import *

"""Place last to ensure all env vars are included in GENERATED_ENV_FIELDS."""
from .generate import *

BASE_DIR = Path.cwd()

ROOT_URLCONF: str = f"{Package.NAME}.contrib.urls"

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
