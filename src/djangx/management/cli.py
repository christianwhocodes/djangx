#!/usr/bin/env python
"""Command-line interface for the project manager.

This module provides the main CLI entry point and command routing logic.
It handles:
- Version display
- Project initialization (startproject/init/new commands)
- Delegation to Management utility commands for everything else

The CLI uses a simple match/case pattern for routing commands, making it
easy to add new top-level commands in the future.
"""

import sys
from typing import NoReturn

from christianwhocodes import ExitCode

from .. import PKG_DISPLAY_NAME, PKG_NAME, PROJECT_DIR


def _handle_startproject() -> ExitCode:
    f"""Handle the 'startproject' command with comprehensive argument parsing and validation.

    This function is the bridge between CLI arguments and the project initialization logic.
    It performs several key responsibilities:

    1. **Argument Parsing**: Defines and parses all CLI flags for project creation
    2. **Validation**: Validates argument combinations at the CLI level
    3. **Translation**: Converts CLI flags to function parameters
    4. **Error Reporting**: Provides clear error messages for invalid combinations

    The validation happens in two stages:
    - CLI-level validation (this function): Catches incompatible flag combinations
    - Prompt-level validation (in startproject.py): Validates interactive choices

    Returns:
        ExitCode from the initialize function (SUCCESS or ERROR).

    Raises:
        SystemExit: Via parser.error() for invalid argument combinations.

    Flow:
        1. Create ArgumentParser with all available flags
        2. Parse sys.argv[2:] (everything after the command name - startproject/init/new )
        3. Validate preset-database compatibility
        4. Validate preset-pg_config compatibility
        5. Convert mutually-exclusive flags to single parameter
        6. Call initialize() with validated parameters

    Example CLI calls:
        $ {PKG_NAME} startproject --preset vercel  # Auto-selects PostgreSQL + env vars
        $ {PKG_NAME} startproject --database postgresql --pg-env-vars
        $ {PKG_NAME} startproject --preset default --database sqlite3
        $ {PKG_NAME} startproject --database sqlite3  # Auto-selects 'default' preset
        $ {PKG_NAME} startproject --force
    """
    from argparse import ArgumentParser, Namespace

    from ..enums import DatabaseBackend, PresetType
    from .commands.startproject import initialize
    from .maps import (
        DATABASE_CONFIGS,
        PG_CONFIG_METHODS,
        PRESET_CONFIGS,
        validate_pg_config_compatibility,
        validate_preset_database_compatibility,
    )

    # ========================================================================
    # Argument Parser Setup
    # ========================================================================

    parser = ArgumentParser(
        prog=f"{PKG_NAME} startproject",
        description=f"Initialize a new {PKG_DISPLAY_NAME} project",
    )

    # ------------------------------------------------------------------------
    # Preset Selection Flag
    # ------------------------------------------------------------------------
    # Determines the project template/configuration to use
    # Maps to: PresetType enum and PRESET_CONFIGS mapping

    preset_help_lines = ["Project preset to use (skips interactive prompt). Options:"]
    for preset_type in PresetType:
        config = PRESET_CONFIGS[preset_type]
        preset_help_lines.append(f"  • {preset_type.value}: {config.description}")

    parser.add_argument(
        "--preset",
        choices=[p.value for p in PresetType],
        help=" ".join(preset_help_lines),
        metavar="PRESET",
    )

    # ------------------------------------------------------------------------
    # Database Backend Flag
    # ------------------------------------------------------------------------
    # Determines which database system to configure
    # Maps to: DatabaseBackend enum and DATABASE_CONFIGS mapping

    db_help_lines = ["Database backend to use (skips interactive prompt). Options:"]
    for db_backend in DatabaseBackend:
        config = DATABASE_CONFIGS[db_backend]
        db_help_lines.append(f"  • {db_backend.value}: {config.description}")
    db_help_lines.append(
        f"\nNote: {PRESET_CONFIGS[PresetType.VERCEL].name} preset requires "
        f"{DatabaseBackend.POSTGRESQL.value}."
    )

    parser.add_argument(
        "--database",
        "--db",
        choices=[db.value for db in DatabaseBackend],
        help=" ".join(db_help_lines),
        metavar="DATABASE",
    )

    # ------------------------------------------------------------------------
    # PostgreSQL Configuration Method Flags (Mutually Exclusive)
    # ------------------------------------------------------------------------
    # Determines how PostgreSQL credentials are managed
    # Maps to: PG_CONFIG_METHODS mapping
    # Only relevant when database=postgresql

    pg_config_group = parser.add_mutually_exclusive_group()

    env_vars_method = PG_CONFIG_METHODS[True]
    pg_config_group.add_argument(
        env_vars_method.cli_flag,
        action="store_true",
        dest="pg_env_vars_flag",
        help=f"{env_vars_method.description} (skips interactive prompt)",
    )

    service_files_method = PG_CONFIG_METHODS[False]
    pg_config_group.add_argument(
        service_files_method.cli_flag,
        action="store_true",
        dest="pg_service_files_flag",
        help=f"{service_files_method.description} (skips interactive prompt)",
    )

    # ------------------------------------------------------------------------
    # Force Flag
    # ------------------------------------------------------------------------
    # Bypasses directory validation checks

    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Skip directory validation and initialize even if directory is not empty",
    )

    # ========================================================================
    # Parse Arguments
    # ========================================================================
    # sys.argv structure: [script_name, command, *args]
    # Example: ['script_name', 'startproject', '--preset', 'vercel']
    # We parse from index 2 onwards to skip 'script_name' and 'startproject'

    args: Namespace = parser.parse_args(sys.argv[2:])

    # ========================================================================
    # CLI-Level Validation and Auto-Configuration
    # ========================================================================
    # We validate incompatible combinations BEFORE calling initialize()
    # This provides immediate feedback at the CLI level

    # Convert string values to enum types for validation
    preset_enum = PresetType(args.preset) if args.preset else None
    database_enum = DatabaseBackend(args.database) if args.database else None

    # ------------------------------------------------------------------------
    # Auto-configure based on preset/database requirements
    # ------------------------------------------------------------------------
    # If database is sqlite3 but no preset specified, auto-select 'default'
    # since 'vercel' preset requires PostgreSQL. This skips the preset prompt.
    if not preset_enum and database_enum == DatabaseBackend.SQLITE3:
        preset_enum = PresetType.DEFAULT
        args.preset = PresetType.DEFAULT.value

    # If preset is vercel but no database specified, auto-select PostgreSQL
    # and environment variables config since Vercel requires both.
    if preset_enum == PresetType.VERCEL:
        if not database_enum:
            database_enum = DatabaseBackend.POSTGRESQL
            args.database = DatabaseBackend.POSTGRESQL.value
        # Auto-select env vars for PostgreSQL if no PG config method specified
        if not args.pg_env_vars_flag and not args.pg_service_files_flag:
            args.pg_env_vars_flag = True

    # ------------------------------------------------------------------------
    # Validate Preset-Database Compatibility
    # ------------------------------------------------------------------------
    if preset_enum and database_enum:
        is_valid, error_msg = validate_preset_database_compatibility(preset_enum, database_enum)
        if not is_valid:
            parser.error(error_msg or "Selected preset and database are not compatible.")

    # ------------------------------------------------------------------------
    # Validate Preset-PostgreSQL Config Compatibility
    # ------------------------------------------------------------------------
    if preset_enum:
        # Check if user specified a PG config method
        if args.pg_env_vars_flag:
            is_valid, error_msg = validate_pg_config_compatibility(preset_enum, True)
            if not is_valid:
                parser.error(
                    error_msg
                    or "Selected preset is not compatible with environment variable configuration."
                )
        elif args.pg_service_files_flag:
            is_valid, error_msg = validate_pg_config_compatibility(preset_enum, False)
            if not is_valid:
                parser.error(
                    error_msg or "Selected preset is not compatible with service file configuration."
                )

    # ========================================================================
    # Convert CLI Flags to Function Parameters
    # ========================================================================
    # The mutually-exclusive flags (--pg-env-vars, --pg-service-files) need
    # to be converted into a single Optional[bool] parameter:
    # - True: use environment variables
    # - False: use service files
    # - None: ask user interactively

    pg_env_vars_value: bool | None = None
    if args.pg_env_vars_flag:
        pg_env_vars_value = True
    elif args.pg_service_files_flag:
        pg_env_vars_value = False

    # ========================================================================
    # Call Initialization Function
    # ========================================================================
    return initialize(
        preset=args.preset,  # str | None
        database=args.database,  # str | None
        pg_env_vars=pg_env_vars_value,  # bool | None
        force=args.force,  # bool
    )


def main() -> NoReturn | None:
    """Main entry point for the CLI.

    Routes commands to appropriate handlers using pattern matching.
    Falls back to Management utility for standard commands.

    Command routing:
    - version/-v/--version: Display package version
    - startproject/init/new: Initialize new project
    - *: Delegate to Management utility commands (runserver, migrate, etc.)

    The routing is designed to be easily extensible - just add new cases
    to the match statement for additional top-level commands.
    """
    match sys.argv[1]:
        # ====================================================================
        # Version Display
        # ====================================================================
        case "-v" | "--version" | "version":
            from christianwhocodes.core import print_version

            sys.exit(print_version(PKG_NAME))

        # ====================================================================
        # Project Initialization
        # ====================================================================
        case "startproject" | "init" | "new":
            sys.exit(_handle_startproject())

        # ====================================================================
        # Management Utility Commands (Fallback)
        # ====================================================================
        # All other commands are passed to Management utility
        # Examples: runserver, migrate, makemigrations, shell, etc.
        case _:
            from os import environ

            from django.core.management import ManagementUtility

            # Add project directory to Python path for imports
            sys.path.insert(0, str(PROJECT_DIR))

            # Set default settings module
            environ.setdefault("DJANGO_SETTINGS_MODULE", f"{PKG_NAME}.settings")

            # Create and execute Management utility
            utility = ManagementUtility(sys.argv)
            utility.prog_name = PKG_NAME
            utility.execute()


if __name__ == "__main__":
    main()
