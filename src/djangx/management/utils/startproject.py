"""Startproject validation utilities."""

from ..enums import DatabaseEnum, PresetEnum
from ..settings import PG_CONFIG_PRESETS, STARTPROJECT_PRESETS

__all__: list[str] = [
    "validate_pg_config_compatibility",
    "validate_preset_database_compatibility",
]


def validate_preset_database_compatibility(
    preset: PresetEnum, database: DatabaseEnum
) -> tuple[bool, str]:
    """Check if a database backend is compatible with a preset."""
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
    """Check if a PG config method is compatible with a preset."""
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
