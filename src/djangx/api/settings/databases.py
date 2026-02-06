# ==============================================================================
# Database Configuration
# https://docs.djangoproject.com/en/stable/ref/databases/#postgresql-notes
# https://www.postgresql.org/docs/current/libpq-pgservice.html
# https://www.postgresql.org/docs/current/libpq-pgpass.html
# ==============================================================================
from ... import PROJECT_DIR, Conf, ConfField
from ..enums import DatabaseBackend
from ..types import DatabaseDict, DatabaseOptionsDict, DatabasesDict


class DatabaseConf(Conf):
    """Database configuration settings."""

    backend = ConfField(
        type=str,
        choices=[DatabaseBackend.SQLITE3, DatabaseBackend.POSTGRESQL],
        env="DB_BACKEND",
        toml="db.backend",
        default=DatabaseBackend.SQLITE3,
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


_DATABASE = DatabaseConf()


def _get_databases_config() -> DatabasesDict:
    """Generate databases configuration based on backend type."""

    backend: str = _DATABASE.backend.lower()

    match backend:
        case DatabaseBackend.SQLITE3:
            return {
                "default": {
                    "ENGINE": f"django.db.backends.{DatabaseBackend.SQLITE3.value}",
                    "NAME": PROJECT_DIR / f"db.{DatabaseBackend.SQLITE3.value}",
                }
            }
        case DatabaseBackend.POSTGRESQL:
            options: DatabaseOptionsDict = {
                "pool": _DATABASE.pool,
                "sslmode": _DATABASE.ssl_mode,
            }

            # Add service or connection vars
            if _DATABASE.use_env_vars:
                config: DatabaseDict = {
                    "ENGINE": f"django.db.backends.{DatabaseBackend.POSTGRESQL.value}",
                    "NAME": _DATABASE.name,
                    "USER": _DATABASE.user,
                    "PASSWORD": _DATABASE.password,
                    "HOST": _DATABASE.host,
                    "PORT": _DATABASE.port,
                    "OPTIONS": options,
                }
            else:
                options["service"] = _DATABASE.service
                config: DatabaseDict = {
                    "ENGINE": f"django.db.backends.{DatabaseBackend.POSTGRESQL.value}",
                    "NAME": _DATABASE.name,
                    "OPTIONS": options,
                }

            return {"default": config}
        case _:
            raise ValueError(f"Unsupported DB backend: {backend}")


DATABASES: DatabasesDict = _get_databases_config()


__all__: list[str] = ["DATABASES"]
