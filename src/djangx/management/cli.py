#!/usr/bin/env python

import sys
from typing import NoReturn, Optional

from .. import PKG_DISPLAY_NAME, PKG_NAME, PROJECT_DIR


def main() -> Optional[NoReturn]:
    """Main entry point for the CLI."""
    match sys.argv[1]:
        case "-v" | "--version" | "version":
            from christianwhocodes.core import print_version

            sys.exit(print_version(PKG_NAME))

        case "startproject" | "init" | "new":
            from argparse import ArgumentParser, Namespace

            from ..enums import DatabaseBackend
            from .commands.startproject import initialize

            parser = ArgumentParser(description=f"Initialize a new {PKG_DISPLAY_NAME} project")
            parser.add_argument(
                "--preset",
                choices=["default", "vercel"],
                help="Project preset to use (skips interactive prompt)",
            )
            parser.add_argument(
                "--database",
                "--db",
                choices=[DatabaseBackend.SQLITE3, DatabaseBackend.POSTGRESQL],
                help=f"Database backend to use (skips interactive prompt). Note: Vercel preset requires {DatabaseBackend.POSTGRESQL.value}.",
            )
            parser.add_argument(
                "--force",
                "-f",
                action="store_true",
                help="Skip directory validation and initialize even if directory is not empty",
            )
            args: Namespace = parser.parse_args(sys.argv[2:])

            sys.exit(initialize(preset=args.preset, database=args.database, force=args.force))

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
