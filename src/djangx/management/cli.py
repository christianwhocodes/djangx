#!/usr/bin/env python

import sys
from typing import NoReturn, Optional

from christianwhocodes import ExitCode

from .. import PKG_DISPLAY_NAME, PKG_NAME, PROJECT_DIR


def _handle_startproject() -> ExitCode:
    """Handle the startproject command with argument parsing.

    Returns:
        Exit code from the initialize function.
    """
    from argparse import ArgumentParser, Namespace

    from ..enums import DatabaseBackend
    from .commands.startproject import initialize

    parser = ArgumentParser(
        prog=f"{PKG_NAME} startproject", description=f"Initialize a new {PKG_DISPLAY_NAME} project"
    )

    parser.add_argument(
        "--preset",
        choices=["default", "vercel"],
        help="Project preset to use (skips interactive prompt)",
    )

    parser.add_argument(
        "--database",
        "--db",
        choices=[db.value for db in DatabaseBackend],
        help=(
            f"Database backend to use (skips interactive prompt). "
            f"Note: Vercel preset requires {DatabaseBackend.POSTGRESQL.value}."
        ),
    )

    # Create mutually exclusive group for PostgreSQL config
    pg_config_group = parser.add_mutually_exclusive_group()
    pg_config_group.add_argument(
        "--pg-env-vars",
        action="store_true",
        dest="pg_env_vars_flag",
        help="Use environment variables for PostgreSQL configuration (skips interactive prompt)",
    )
    pg_config_group.add_argument(
        "--pg-service-files",
        action="store_true",
        dest="pg_service_files_flag",
        help="Use .pg_service.conf and pgpass.conf for PostgreSQL configuration (skips interactive prompt)",
    )

    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Skip directory validation and initialize even if directory is not empty",
    )

    # Parse arguments (excluding the command name itself)
    args: Namespace = parser.parse_args(sys.argv[2:])

    # Validate Vercel preset compatibility
    if args.preset == "vercel":
        if args.database == DatabaseBackend.SQLITE3.value:
            parser.error(
                f"Vercel preset requires {DatabaseBackend.POSTGRESQL.value} database. "
                f"Cannot use --database {DatabaseBackend.SQLITE3.value} with --preset vercel"
            )
        if args.pg_service_files_flag:
            parser.error(
                "Vercel preset requires environment variables. "
                "Cannot use --pg-service-files with --preset vercel"
            )

    # Convert flags to the pg_env_vars parameter
    pg_env_vars_value = None
    if args.pg_env_vars_flag:
        pg_env_vars_value = True
    elif args.pg_service_files_flag:
        pg_env_vars_value = False

    return initialize(
        preset=args.preset,
        database=args.database,
        pg_env_vars=pg_env_vars_value,
        force=args.force,
    )


def main() -> Optional[NoReturn]:
    """Main entry point for the CLI."""
    match sys.argv[1]:
        case "-v" | "--version" | "version":
            from christianwhocodes.core import print_version

            sys.exit(print_version(PKG_NAME))

        case "startproject" | "init" | "new":
            sys.exit(_handle_startproject())

        case _:
            from os import environ

            from django.core.management import ManagementUtility

            sys.path.insert(0, str(PROJECT_DIR))
            environ.setdefault("DJANGO_SETTINGS_MODULE", f"{PKG_NAME}.settings")

            utility = ManagementUtility(sys.argv)
            utility.prog_name = PKG_NAME
            utility.execute()


if __name__ == "__main__":
    main()
