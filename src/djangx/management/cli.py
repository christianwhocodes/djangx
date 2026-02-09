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

from .. import PACKAGE, PROJECT


def main() -> None:
    """Main entry point for the CLI.

    Routes commands to appropriate handlers using pattern matching.
    Falls back to Management utility for standard commands.

    Command routing:
    - version/-v/--version: Display package version
    - startproject/init/new: Initialize new project
    - *: Delegate to Management utility commands (runserver, migrate, etc.)
    """
    match sys.argv[1]:
        # ====================================================================
        # Version Display
        # ====================================================================
        case "-v" | "--version" | "version":
            from christianwhocodes import print_version

            sys.exit(print_version(PACKAGE.name))

        # ====================================================================
        # Project Initialization
        # ====================================================================
        case "startproject" | "init" | "new":
            from .commands import handle_startproject

            sys.exit(handle_startproject())

        # ====================================================================
        # Management Utility Commands (Fallback)
        # ====================================================================
        # All other commands are passed to Management utility
        # Examples: runserver, migrate, makemigrations, shell, etc.
        case _:
            from os import environ

            from django.core.management import ManagementUtility

            # Add project directory to Python path for imports
            sys.path.insert(0, str(PROJECT.base_dir))

            # Set default settings module
            environ.setdefault("DJANGO_SETTINGS_MODULE", f"{PACKAGE.name}.management.settings")

            # Create and execute Management utility
            utility = ManagementUtility(sys.argv)
            utility.prog_name = PACKAGE.name
            utility.execute()


if __name__ == "__main__":
    main()
