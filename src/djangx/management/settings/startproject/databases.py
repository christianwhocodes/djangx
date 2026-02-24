"""Databases settings."""

from pathlib import Path
from typing import NotRequired, TypedDict

from ....constants import DatabaseChoices, Project
from ...conf import BaseConf, ConfField

__all__: list[str] = ["DATABASES"]


class _DatabaseConf(BaseConf):
    """Database settings."""

    backend = ConfField(
        type=str,
        choices=[DatabaseChoices.SQLITE3, DatabaseChoices.POSTGRESQL],
        env="DB_BACKEND",
        toml="db.backend",
        default=DatabaseChoices.SQLITE3,
    )
    # postgresql specific
    use_env_vars = ConfField(
        type=bool,
        env="DB_USE_ENV_VARS",
        toml="db.use-env-vars",
        default=False,
    )
    service = ConfField(
        type=str,
        env="DB_SERVICE",
        toml="db.service",
        default="",
    )
    user = ConfField(
        type=str,
        env="DB_USER",
        default="",
    )
    password = ConfField(
        type=str,
        env="DB_PASSWORD",
        default="",
    )
    name = ConfField(
        type=str,
        env="DB_NAME",
        default="",
    )
    host = ConfField(
        type=str,
        env="DB_HOST",
        default="",
    )
    port = ConfField(
        type=str,
        env="DB_PORT",
        default="",
    )
    pool = ConfField(
        type=bool,
        env="DB_POOL",
        toml="db.pool",
        default=False,
    )
    ssl_mode = ConfField(
        type=str,
        env="DB_SSL_MODE",
        toml="db.ssl-mode",
        default="prefer",
    )


_DATABASE = _DatabaseConf()


class _DatabaseOptionsDict(TypedDict, total=False):
    """Database OPTIONS dict."""

    service: str
    pool: bool
    sslmode: str


class _DatabaseDict(TypedDict):
    """Single database configuration entry."""

    ENGINE: str
    NAME: str | Path
    USER: NotRequired[str | None]
    PASSWORD: NotRequired[str | None]
    HOST: NotRequired[str | None]
    PORT: NotRequired[str | None]
    OPTIONS: NotRequired[_DatabaseOptionsDict]


class _DatabasesDict(TypedDict):
    """DATABASES setting dict."""

    default: _DatabaseDict


def _get_databases_config() -> _DatabasesDict:
    """Build the DATABASES setting based on configured backend."""
    backend: str = _DATABASE.backend.lower()

    match backend:
        case DatabaseChoices.SQLITE3:
            return {
                "default": {
                    "ENGINE": f"django.db.backends.{DatabaseChoices.SQLITE3}",
                    "NAME": Project.BASE_DIR / f"db.{DatabaseChoices.SQLITE3}",
                }
            }
        case DatabaseChoices.POSTGRESQL:
            options: _DatabaseOptionsDict = {
                "pool": _DATABASE.pool,
                "sslmode": _DATABASE.ssl_mode,
            }

            # Add service or connection vars
            config: _DatabaseDict
            if _DATABASE.use_env_vars:
                config = {
                    "ENGINE": f"django.db.backends.{DatabaseChoices.POSTGRESQL}",
                    "NAME": _DATABASE.name,
                    "USER": _DATABASE.user,
                    "PASSWORD": _DATABASE.password,
                    "HOST": _DATABASE.host,
                    "PORT": _DATABASE.port,
                    "OPTIONS": options,
                }
            else:
                options["service"] = _DATABASE.service
                config = {
                    "ENGINE": f"django.db.backends.{DatabaseChoices.POSTGRESQL}",
                    "NAME": _DATABASE.name,
                    "OPTIONS": options,
                }

            return {"default": config}
        case _:
            raise ValueError(f"Unsupported DB backend: {backend}")


DATABASES: _DatabasesDict = _get_databases_config()


# ==============================================================================
# Database Configuration
# https://docs.djangoproject.com/en/stable/ref/databases/#postgresql-notes
# https://www.postgresql.org/docs/current/libpq-pgservice.html
# https://www.postgresql.org/docs/current/libpq-pgpass.html
# ==============================================================================
