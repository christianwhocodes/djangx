# ==============================================================================
# Database Configuration
# https://docs.djangoproject.com/en/stable/ref/databases/#postgresql-notes
# https://www.postgresql.org/docs/current/libpq-pgservice.html
# https://www.postgresql.org/docs/current/libpq-pgpass.html
# ==============================================================================
from pathlib import Path

from ... import Conf, ConfField
from ..types import DatabaseDict, DatabaseOptionsDict, DatabasesDict


class DatabaseConf(Conf):
    """Database configuration settings."""

    backend = ConfField(
        choices=["sqlite3", "postgresql"],
        env="DB_BACKEND",
        toml="db.backend",
        default="sqlite3",
        type=str,
    )
    use_vars = ConfField(env="DB_USE_VARS", toml="db.use-vars", type=bool)
    service = ConfField(env="DB_SERVICE", toml="db.service", type=str)
    user = ConfField(env="DB_USER", type=str)
    password = ConfField(env="DB_PASSWORD", type=str)
    name = ConfField(env="DB_NAME", type=str)
    host = ConfField(env="DB_HOST", type=str)
    port = ConfField(env="DB_PORT", type=str)
    pool = ConfField(env="DB_POOL", toml="db.pool", type=bool)
    ssl_mode = ConfField(env="DB_SSL_MODE", toml="db.ssl-mode", default="prefer", type=str)


_DATABASE = DatabaseConf()


def _get_databases_config() -> DatabasesDict:
    """Generate databases configuration based on backend type."""

    backend: str = _DATABASE.backend.lower()

    match backend:
        case "sqlite" | "sqlite3":
            return {
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": Path.cwd() / "db.sqlite3",
                }
            }
        case "postgresql" | "postgres" | "psql" | "pgsql" | "pg" | "psycopg":
            options: DatabaseOptionsDict = {
                "pool": _DATABASE.pool,
                "sslmode": _DATABASE.ssl_mode,
            }

            # Add service or connection vars
            if _DATABASE.use_vars:
                config: DatabaseDict = {
                    "ENGINE": "django.db.backends.postgresql",
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
                    "ENGINE": "django.db.backends.postgresql",
                    "NAME": _DATABASE.name,
                    "OPTIONS": options,
                }

            return {"default": config}
        case _:
            raise ValueError(f"Unsupported DB backend: {backend}")


DATABASES: DatabasesDict = _get_databases_config()


__all__: list[str] = ["DATABASES"]
