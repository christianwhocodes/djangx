# ==============================================================================
# Security & deployment checklist
# See https://docs.djangoproject.com/en/stable/howto/deployment/checklist/
# ==============================================================================

from ... import Conf, ConfField


class SecurityConf(Conf):
    """Security-related configuration settings."""

    secret_key = ConfField(
        env="SECRET_KEY",
        toml="secret-key",
        default="django-insecure-change-me-in-production-via-env-variable",
        type=str,
    )
    debug = ConfField(env="DEBUG", toml="debug", default=True, type=bool)
    allowed_hosts = ConfField(
        env="ALLOWED_HOSTS",
        toml="allowed-hosts",
        default=["localhost", "127.0.0.1"],
        type=list,
    )
    secure_ssl_redirect = ConfField(
        env="SECURE_SSL_REDIRECT",
        toml="secure-ssl-redirect",
        default=False,
        type=bool,
    )
    session_cookie_secure = ConfField(
        env="SESSION_COOKIE_SECURE",
        toml="session-cookie-secure",
        default=False,
        type=bool,
    )
    csrf_cookie_secure = ConfField(
        env="CSRF_COOKIE_SECURE",
        toml="csrf-cookie-secure",
        default=False,
        type=bool,
    )
    secure_hsts_seconds = ConfField(
        env="SECURE_HSTS_SECONDS",
        toml="secure-hsts-seconds",
        type=int,
    )


_SECURITY = SecurityConf()

SECRET_KEY: str = _SECURITY.secret_key
DEBUG: bool = _SECURITY.debug
ALLOWED_HOSTS: list[str] = _SECURITY.allowed_hosts
SECURE_SSL_REDIRECT: bool = _SECURITY.secure_ssl_redirect
SESSION_COOKIE_SECURE: bool = _SECURITY.session_cookie_secure
CSRF_COOKIE_SECURE: bool = _SECURITY.csrf_cookie_secure
SECURE_HSTS_SECONDS: int = _SECURITY.secure_hsts_seconds


__all__: list[str] = [
    "SECRET_KEY",
    "DEBUG",
    "ALLOWED_HOSTS",
    "SECURE_SSL_REDIRECT",
    "SESSION_COOKIE_SECURE",
    "CSRF_COOKIE_SECURE",
    "SECURE_HSTS_SECONDS",
]
