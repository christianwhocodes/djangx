"""Databases settings."""

from .... import PROJECT
from ...conf import ConfField, ManagementConf
from ...definitions import DatabaseDict, DatabaseOptionsDict, DatabasesDict
from ...enums import DatabaseEnum

# ==============================================================================
# Database Configuration
# https://docs.djangoproject.com/en/stable/ref/databases/#postgresql-notes
# https://www.postgresql.org/docs/current/libpq-pgservice.html
# https://www.postgresql.org/docs/current/libpq-pgpass.html
# ==============================================================================


class _DatabaseConf(ManagementConf):
    """Database settings."""

    backend = ConfField(
        type=str,
        choices=[DatabaseEnum.SQLITE3, DatabaseEnum.POSTGRESQL],
        env="DB_BACKEND",
        toml="db.backend",
        default=DatabaseEnum.SQLITE3,
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


def _get_databases_config() -> DatabasesDict:
    """Build the DATABASES setting based on configured backend."""
    backend: str = _DATABASE.backend.lower()

    match backend:
        case DatabaseEnum.SQLITE3:
            return {
                "default": {
                    "ENGINE": f"django.db.backends.{DatabaseEnum.SQLITE3.value}",
                    "NAME": PROJECT.base_dir / f"db.{DatabaseEnum.SQLITE3.value}",
                }
            }
        case DatabaseEnum.POSTGRESQL:
            options: DatabaseOptionsDict = {
                "pool": _DATABASE.pool,
                "sslmode": _DATABASE.ssl_mode,
            }

            # Add service or connection vars
            if _DATABASE.use_env_vars:
                config: DatabaseDict = {
                    "ENGINE": f"django.db.backends.{DatabaseEnum.POSTGRESQL.value}",
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
                    "ENGINE": f"django.db.backends.{DatabaseEnum.POSTGRESQL.value}",
                    "NAME": _DATABASE.name,
                    "OPTIONS": options,
                }

            return {"default": config}
        case _:
            raise ValueError(f"Unsupported DB backend: {backend}")


DATABASES: DatabasesDict = _get_databases_config()


__all__: list[str] = ["DATABASES"]
