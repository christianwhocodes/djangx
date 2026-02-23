"""Start Project mappings."""

from dataclasses import dataclass
from typing import Final

from christianwhocodes import PostgresFilename

from ... import PACKAGE
from ..enums import DatabaseEnum, PresetEnum

__all__: list[str] = [
    "DATABASE_ENUM_CONFIG_MAP",
    "PG_CONFIG_METHOD_MAP",
    "PRESET_ENUM_CONFIG_MAP",
]


@dataclass(frozen=True)
class _PresetDataclass:
    """Project preset configuration."""

    preset: PresetEnum
    name: str
    description: str
    required_database: DatabaseEnum | None
    required_pg_config: bool | None
    dependencies: tuple[str, ...]
    generated_files: tuple[str, ...]
    learn_more_url: str | None


@dataclass(frozen=True)
class _DatabaseConfig:
    """Database backend configuration."""

    backend: DatabaseEnum
    name: str
    description: str
    dependencies: tuple[str, ...]
    requires_pg_config: bool
    learn_more_url: str | None


@dataclass(frozen=True)
class _PGConfigMethod:
    """PostgreSQL configuration method."""

    value: bool
    name: str
    description: str
    cli_flag: str
    files_required: tuple[str, ...]
    learn_more_url: str | None


PRESET_ENUM_CONFIG_MAP: Final[dict[PresetEnum, _PresetDataclass]] = {
    PresetEnum.DEFAULT: _PresetDataclass(
        preset=PresetEnum.DEFAULT,
        name="Default",
        description=f"Standard {PACKAGE.display_name} project with sensible defaults",
        required_database=None,  # Can use any database
        required_pg_config=None,  # PG config method is user's choice
        dependencies=(),
        generated_files=("pyproject.toml", ".gitignore", "README.md", ".env.example"),
        learn_more_url=None,
    ),
    PresetEnum.VERCEL: _PresetDataclass(
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


DATABASE_ENUM_CONFIG_MAP: Final[dict[DatabaseEnum, _DatabaseConfig]] = {
    DatabaseEnum.SQLITE3: _DatabaseConfig(
        backend=DatabaseEnum.SQLITE3,
        name="SQLite",
        description="Lightweight file-based database, perfect for development and small projects",
        dependencies=(),  # Built into Python
        requires_pg_config=False,
        learn_more_url="https://docs.djangoproject.com/en/stable/ref/databases/#sqlite-notes",
    ),
    DatabaseEnum.POSTGRESQL: _DatabaseConfig(
        backend=DatabaseEnum.POSTGRESQL,
        name="PostgreSQL",
        description="Production-grade relational database with advanced features",
        dependencies=("psycopg[binary,pool]>=3.3.2",),
        requires_pg_config=True,
        learn_more_url="https://docs.djangoproject.com/en/stable/ref/databases/#postgresql-notes",
    ),
}


PG_CONFIG_METHOD_MAP: Final[dict[bool, _PGConfigMethod]] = {
    True: _PGConfigMethod(
        value=True,
        name="Environment Variables",
        description="Store PostgreSQL credentials in .env file",
        cli_flag="--pg-env-vars",
        files_required=(),
        learn_more_url=None,
    ),
    False: _PGConfigMethod(
        value=False,
        name="PostgreSQL Service Files",
        description=f"Use `{PostgresFilename.PGSERVICE}` and `{PostgresFilename.PGPASS}` files",
        cli_flag="--pg-service-files",
        files_required=(PostgresFilename.PGSERVICE, PostgresFilename.PGPASS),
        learn_more_url="https://www.postgresql.org/docs/current/libpq-pgservice.html\n   https://www.postgresql.org/docs/current/libpq-pgpass.html",
    ),
}
