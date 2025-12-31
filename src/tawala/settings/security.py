# ==============================================================================
# Security & deployment checklist
# See https://docs.djangoproject.com/en/stable/howto/deployment/checklist/
# ==============================================================================
from typing import TypedDict

from .conf import Conf, ConfField


class SecurityConf(Conf):
    """Security-related configuration settings."""

    secret_key = ConfField(env="SECRET_KEY", toml="secret-key", type=str)
    debug = ConfField(env="DEBUG", toml="debug", type=bool)
    allowed_hosts = ConfField(env="ALLOWED_HOSTS", toml="allowed-hosts", type="list[str]")


_security = SecurityConf()


class SecurityDict(TypedDict):
    """Type definition for security settings."""

    secret_key: str
    debug: bool
    allowed_hosts: list[str]
    secure_ssl_redirect: bool
    session_cookie_secure: bool
    csrf_cookie_secure: bool
    secure_hsts_seconds: int


SECURITY: SecurityDict = {
    "secret_key": _security.secret_key,
    "debug": _security.debug,
    "allowed_hosts": _security.allowed_hosts,
    "secure_ssl_redirect": True if not _security.debug else False,
    "session_cookie_secure": True if not _security.debug else False,
    "csrf_cookie_secure": True if not _security.debug else False,
    "secure_hsts_seconds": 3600 if not _security.debug else 0,
}


SECRET_KEY: str = SECURITY["secret_key"]
DEBUG: bool = SECURITY["debug"]
ALLOWED_HOSTS: list[str] = SECURITY["allowed_hosts"]
SECURE_SSL_REDIRECT: bool = SECURITY.get("secure_ssl_redirect")
SESSION_COOKIE_SECURE: bool = SECURITY.get("session_cookie_secure")
CSRF_COOKIE_SECURE: bool = SECURITY.get("csrf_cookie_secure")
SECURE_HSTS_SECONDS: int = SECURITY.get("secure_hsts_seconds")

__all__ = [
    "SECURITY",
    "SECRET_KEY",
    "DEBUG",
    "ALLOWED_HOSTS",
    "SECURE_SSL_REDIRECT",
    "SESSION_COOKIE_SECURE",
    "CSRF_COOKIE_SECURE",
    "SECURE_HSTS_SECONDS",
]
