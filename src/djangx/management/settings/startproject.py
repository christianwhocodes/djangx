"""Startproject settings configuration."""

# ==============================================================================
# Database Configuration
# https://docs.djangoproject.com/en/stable/ref/databases/#postgresql-notes
# https://www.postgresql.org/docs/current/libpq-pgservice.html
# https://www.postgresql.org/docs/current/libpq-pgpass.html
# ==============================================================================

from typing import Final

from christianwhocodes import PgConfigFilesEnum

from ... import PACKAGE, PROJECT
from ..enums import DatabaseEnum, PresetEnum
from ..types import (
    DatabaseDataclass,
    DatabaseDict,
    DatabaseOptionsDict,
    DatabasesDict,
    PGConfigMethodDataclass,
    PresetDataclass,
)
from .config import ConfField, SettingConfig

__all__: list[str] = ["DATABASES", "DATABASE_PRESETS", "PG_CONFIG_PRESETS", "STARTPROJECT_PRESETS"]


STARTPROJECT_PRESETS: Final[dict[PresetEnum, PresetDataclass]] = {
    PresetEnum.DEFAULT: PresetDataclass(
        preset=PresetEnum.DEFAULT,
        name="Default",
        description=f"Standard {PACKAGE.display_name} project with sensible defaults",
        required_database=None,  # Can use any database
        required_pg_config=None,  # PG config method is user's choice
        dependencies=(),
        generated_files=("pyproject.toml", ".gitignore", "README.md", ".env.example"),
        learn_more_url=None,
    ),
    PresetEnum.VERCEL: PresetDataclass(
        preset=PresetEnum.VERCEL,
        name="Vercel",
        description="Optimized for deployment on Vercel serverless platform",
        required_database=DatabaseEnum.POSTGRESQL,  # Vercel needs PostgreSQL
        required_pg_config=True,  # Vercel requires env vars (no filesystem)
        dependencies=("vercel>=0.3.8",),
        generated_files=(
            "pyproject.toml",
            ".gitignore",
            "README.md",
            ".env.example",
            "vercel.json",
            "api/server.py",
        ),
        learn_more_url="https://to-be-added.example/docs",
    ),
}


class _DatabaseConf(SettingConfig):
    """Database configuration settings."""

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
    """Generate databases configuration based on backend type."""
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
                config: DatabaseDict = {
                    "ENGINE": f"django.db.backends.{DatabaseEnum.POSTGRESQL.value}",
                    "NAME": _DATABASE.name,
                    "OPTIONS": options,
                }

            return {"default": config}
        case _:
            raise ValueError(f"Unsupported DB backend: {backend}")


DATABASES: DatabasesDict = _get_databases_config()


DATABASE_PRESETS: Final[dict[DatabaseEnum, DatabaseDataclass]] = {
    DatabaseEnum.SQLITE3: DatabaseDataclass(
        backend=DatabaseEnum.SQLITE3,
        name="SQLite",
        description="Lightweight file-based database, perfect for development and small projects",
        dependencies=(),  # Built into Python
        requires_pg_config=False,
        learn_more_url="https://docs.djangoproject.com/en/stable/ref/databases/#sqlite-notes",
    ),
    DatabaseEnum.POSTGRESQL: DatabaseDataclass(
        backend=DatabaseEnum.POSTGRESQL,
        name="PostgreSQL",
        description="Production-grade relational database with advanced features",
        dependencies=("psycopg[binary,pool]>=3.3.2",),
        requires_pg_config=True,
        learn_more_url="https://docs.djangoproject.com/en/stable/ref/databases/#postgresql-notes",
    ),
}


PG_CONFIG_PRESETS: Final[dict[bool, PGConfigMethodDataclass]] = {
    True: PGConfigMethodDataclass(
        value=True,
        name="Environment Variables",
        description="Store PostgreSQL credentials in .env file",
        cli_flag="--pg-env-vars",
        files_required=(),
        learn_more_url=None,
    ),
    False: PGConfigMethodDataclass(
        value=False,
        name="PostgreSQL Service Files",
        description=f"Use {PgConfigFilesEnum.PG_SERVICE} and {PgConfigFilesEnum.PGPASS} files",
        cli_flag="--pg-service-files",
        files_required=(PgConfigFilesEnum.PG_SERVICE, PgConfigFilesEnum.PGPASS),
        learn_more_url="https://www.postgresql.org/docs/current/libpq-pgservice.html\nhttps://www.postgresql.org/docs/current/libpq-pgpass.html",
    ),
}
