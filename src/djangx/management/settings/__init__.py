"""Settings configuration."""

from pathlib import Path

from django.utils.csp import CSP  # pyright: ignore[reportMissingTypeStubs]

from ... import PROJECT
from .api import *  # noqa: F403
from .appdef import *  # noqa: F403
from .auth import *  # noqa: F403
from .runcommands import *  # noqa: F403
from .security import *  # noqa: F403
from .startproject import *  # noqa: F403
from .storages import *  # noqa: F403
from .tailwindcss import *  # noqa: F403

BASE_DIR: Path = PROJECT.base_dir

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
