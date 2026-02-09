"""Utility functions for startproject command."""

from ..enums import DatabaseEnum, PresetEnum
from ..settings import PG_CONFIG_PRESETS, STARTPROJECT_PRESETS

__all__: list[str] = [
    "validate_pg_config_compatibility",
    "validate_preset_database_compatibility",
]


def validate_preset_database_compatibility(
    preset: PresetEnum, database: DatabaseEnum
) -> tuple[bool, str]:
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
    preset_config = STARTPROJECT_PRESETS[preset]

    if preset_config.required_database is None:
        return True, ""

    if preset_config.required_database != database:
        error_msg = (
            f"{preset_config.name} preset requires {preset_config.required_database.value} database. "
            f"Cannot use {database.value} with this preset."
        )
        return False, error_msg

    return True, ""


def validate_pg_config_compatibility(preset: PresetEnum, pg_env_vars: bool) -> tuple[bool, str]:
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
    preset_config = STARTPROJECT_PRESETS[preset]

    if preset_config.required_pg_config is None:
        return True, ""

    if preset_config.required_pg_config != pg_env_vars:
        pg_method = PG_CONFIG_PRESETS[pg_env_vars]
        required_method = PG_CONFIG_PRESETS[preset_config.required_pg_config]

        error_msg = (
            f"{preset_config.name} preset requires {required_method.name}. "
            f"Cannot use {pg_method.cli_flag} with this preset."
        )
        return False, error_msg

    return True, ""
