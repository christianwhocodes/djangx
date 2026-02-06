"""Configuration mappings for project initialization.

This module centralizes all configuration options, validation rules, and
documentation links for different presets and database backends. It provides
a single source of truth for what options are available and compatible with
each configuration.

The mapping structure is designed to be:
- Readable: Clear hierarchical organization
- Understandable: Comprehensive documentation
- Expandable: Easy to add new presets, databases, or config options
"""

from dataclasses import dataclass
from typing import Final

from djangx import PKG_DISPLAY_NAME

from ..enums import DatabaseBackend, PGServiceFilename, PresetType

__all__ = [
    "PresetConfig",
    "DatabaseConfig",
    "PGConfigMethod",
    "PRESET_CONFIGS",
    "DATABASE_CONFIGS",
    "PG_CONFIG_METHODS",
    "validate_preset_database_compatibility",
    "validate_pg_config_compatibility",
]


# ============================================================================
# PostgreSQL Configuration Methods
# ============================================================================


@dataclass(frozen=True)
class PGConfigMethod:
    """PostgreSQL configuration method definition.

    Attributes:
        value: The boolean value (True = env vars, False = service files)
        name: Human-readable name
        description: Detailed description
        cli_flag: CLI flag name for this method
        files_required: List of config files needed (empty for env vars)
        learn_more_url: Documentation URL
    """

    value: bool
    name: str
    description: str
    cli_flag: str
    files_required: tuple[str, ...]
    learn_more_url: str | None


# PostgreSQL configuration methods mapping
PG_CONFIG_METHODS: Final[dict[bool, PGConfigMethod]] = {
    True: PGConfigMethod(
        value=True,
        name="Environment Variables",
        description="Store PostgreSQL credentials in .env file",
        cli_flag="--pg-env-vars",
        files_required=(),
        learn_more_url=None,
    ),
    False: PGConfigMethod(
        value=False,
        name="PostgreSQL Service Files",
        description=f"Use {PGServiceFilename.PG_SERVICE} and {PGServiceFilename.PG_PASS} files",
        cli_flag="--pg-service-files",
        files_required=(PGServiceFilename.PG_SERVICE, PGServiceFilename.PG_PASS),
        learn_more_url="https://www.postgresql.org/docs/current/libpq-pgservice.html",
    ),
}


# ============================================================================
# Database Backend Configurations
# ============================================================================


@dataclass(frozen=True)
class DatabaseConfig:
    """Database backend configuration definition.

    Attributes:
        backend: The database backend enum value
        name: Human-readable display name
        description: Brief description of when to use this database
        dependencies: Python packages required for this database
        requires_pg_config: Whether PostgreSQL config method is needed
        learn_more_url: Documentation URL for this database
    """

    backend: DatabaseBackend
    name: str
    description: str
    dependencies: tuple[str, ...]
    requires_pg_config: bool
    learn_more_url: str | None


# Database backend configurations mapping
DATABASE_CONFIGS: Final[dict[DatabaseBackend, DatabaseConfig]] = {
    DatabaseBackend.SQLITE3: DatabaseConfig(
        backend=DatabaseBackend.SQLITE3,
        name="SQLite",
        description="Lightweight file-based database, perfect for development and small projects",
        dependencies=(),  # Built into Python
        requires_pg_config=False,
        learn_more_url="https://docs.djangoproject.com/en/stable/ref/databases/#sqlite-notes",
    ),
    DatabaseBackend.POSTGRESQL: DatabaseConfig(
        backend=DatabaseBackend.POSTGRESQL,
        name="PostgreSQL",
        description="Production-grade relational database with advanced features",
        dependencies=("psycopg[binary,pool]>=3.3.2",),
        requires_pg_config=True,
        learn_more_url="https://docs.djangoproject.com/en/stable/ref/databases/#postgresql-notes",
    ),
}


# ============================================================================
# Preset Configurations
# ============================================================================


@dataclass(frozen=True)
class PresetConfig:
    """Project preset configuration definition.

    Attributes:
        preset: The preset type enum value
        name: Human-readable display name
        description: Brief description of this preset
        required_database: Required database backend (None = any)
        required_pg_config: Required PG config method (None = any)
        dependencies: Additional Python packages for this preset
        generated_files: Files that will be generated for this preset
        learn_more_url: Documentation URL for this preset
    """

    preset: PresetType
    name: str
    description: str
    required_database: DatabaseBackend | None
    required_pg_config: bool | None
    dependencies: tuple[str, ...]
    generated_files: tuple[str, ...]
    learn_more_url: str | None


# Preset configurations mapping
PRESET_CONFIGS: Final[dict[PresetType, PresetConfig]] = {
    PresetType.DEFAULT: PresetConfig(
        preset=PresetType.DEFAULT,
        name="Default",
        description=f"Standard {PKG_DISPLAY_NAME} project with sensible defaults",
        required_database=None,  # Can use any database
        required_pg_config=None,  # PG config method is user's choice
        dependencies=(),
        generated_files=("pyproject.toml", ".gitignore", "README.md", ".env.example"),
        learn_more_url=None,
    ),
    PresetType.VERCEL: PresetConfig(
        preset=PresetType.VERCEL,
        name="Vercel",
        description="Optimized for deployment on Vercel serverless platform",
        required_database=DatabaseBackend.POSTGRESQL,  # Vercel needs PostgreSQL
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


# ============================================================================
# Validation Functions
# ============================================================================


def validate_preset_database_compatibility(
    preset: PresetType, database: DatabaseBackend
) -> tuple[bool, str | None]:
    """Validate that a database backend is compatible with a preset.

    Args:
        preset: The chosen preset type
        database: The chosen database backend

    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.

    Example:
        >>> is_valid, error = validate_preset_database_compatibility(
        ...     PresetType.VERCEL, DatabaseBackend.SQLITE3
        ... )
        >>> print(is_valid)  # False
        >>> print(error)  # "Vercel preset requires PostgreSQL database..."
    """
    preset_config = PRESET_CONFIGS[preset]

    if preset_config.required_database is None:
        return True, None

    if preset_config.required_database != database:
        error_msg = (
            f"{preset_config.name} preset requires {preset_config.required_database.value} database. "
            f"Cannot use {database.value} with this preset."
        )
        return False, error_msg

    return True, None


def validate_pg_config_compatibility(
    preset: PresetType, pg_env_vars: bool
) -> tuple[bool, str | None]:
    """Validate that a PostgreSQL config method is compatible with a preset.

    Args:
        preset: The chosen preset type
        pg_env_vars: Whether using environment variables for PostgreSQL

    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.

    Example:
        >>> is_valid, error = validate_pg_config_compatibility(
        ...     PresetType.VERCEL, False
        ... )
        >>> print(is_valid)  # False
        >>> print(error)  # "Vercel preset requires environment variables..."
    """
    preset_config = PRESET_CONFIGS[preset]

    if preset_config.required_pg_config is None:
        return True, None

    if preset_config.required_pg_config != pg_env_vars:
        pg_method = PG_CONFIG_METHODS[pg_env_vars]
        required_method = PG_CONFIG_METHODS[preset_config.required_pg_config]

        error_msg = (
            f"{preset_config.name} preset requires {required_method.name}. "
            f"Cannot use {pg_method.cli_flag} with this preset."
        )
        return False, error_msg

    return True, None
