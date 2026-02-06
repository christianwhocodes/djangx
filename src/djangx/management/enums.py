"""Enumeration types.

This module defines all enum types used throughout the framework, including:
- Database backends
- Project presets
- PostgreSQL configuration files
- Apps, context processors, and middleware
- File generation options
"""

from enum import StrEnum
from platform import system

from christianwhocodes.generators import FileGeneratorOption

__all__: list[str] = [
    "FileOption",
    "PresetType",
    "PGServiceFilename",
    "Apps",
    "ContextProcessors",
    "Middlewares",
]

# ============================================================================
# Project Configuration
# ============================================================================


class PresetType(StrEnum):
    """Available project presets.

    Each preset defines a template configuration with specific:
    - Dependencies
    - Generated files
    - Database requirements
    - Configuration settings

    Used in:
    - CLI flags (--preset)
    - Interactive prompts
    - PRESET_CONFIGS mapping (maps.py)
    """

    DEFAULT = "default"
    VERCEL = "vercel"


class PGServiceFilename(StrEnum):
    """PostgreSQL service configuration filenames.

    These files are used when PostgreSQL is configured via service files
    rather than environment variables.

    Platform-specific:
    - Windows: pgpass.conf (no dot prefix)
    - Unix/Linux/Mac: .pgpass (hidden file)

    Used in:
    - PG_CONFIG_METHODS mapping (maps.py)
    - File generation
    - Documentation and help text
    """

    PG_PASS = "pgpass.conf" if system() == "Windows" else ".pgpass"
    PG_SERVICE = ".pg_service.conf"


# ============================================================================
# File Generation
# ============================================================================


class FileOption(StrEnum):
    """File generation options.

    These values are used with the framework's file generation system
    to create various configuration and deployment files.

    Inherited from christianwhocodes.generators:
    - PG_SERVICE: PostgreSQL service configuration
    - PGPASS: PostgreSQL password file
    - SSH_CONFIG: SSH configuration

    Framework-specific:
    - ENV: Environment variables file
    - SERVER: Server deployment file
    - VERCEL: Vercel configuration
    """

    PG_SERVICE = FileGeneratorOption.PG_SERVICE.value
    PGPASS = FileGeneratorOption.PGPASS.value
    SSH_CONFIG = FileGeneratorOption.SSH_CONFIG.value
    ENV = "env"
    SERVER = "server"
    VERCEL = "vercel"


# ============================================================================
# Apps, Context Processors, and Middleware
# ============================================================================


class Apps(StrEnum):
    """Applications enumeration.

    Standard contrib apps plus framework-specific apps.

    Used in:
    - INSTALLED_APPS settings
    - App configuration
    """

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


class ContextProcessors(StrEnum):
    """Template context processors enumeration.

    Used in:
    - TEMPLATES settings
    - Template configuration
    """

    DEBUG = "django.template.context_processors.debug"
    REQUEST = "django.template.context_processors.request"
    AUTH = "django.contrib.auth.context_processors.auth"
    MESSAGES = "django.contrib.messages.context_processors.messages"
    CSP = "django.template.context_processors.csp"


class Middlewares(StrEnum):
    """Middleware enumeration.

    Order matters! This enum lists middleware in the recommended order
    for applications.

    Used in:
    - MIDDLEWARE settings
    - Middleware configuration
    """

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
