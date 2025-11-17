#!/usr/bin/env python
"""
Tawala CLI - Package Commands Executor.

This module provides a filtered Django management interface that only exposes
commands from the tawala.scripts application when run from the package directory.
"""

import os
import sys
from typing import Dict

from django.conf import settings
from django.core import management
from django.core.management import ManagementUtility

# If Django isn't installed, the imports above will fail immediately


class PackageConfig:
    """Configuration for the Tawala CLI."""

    INSTALLED_APPS = ["tawala.scripts"]
    SETTINGS_MODULE = __name__


def configure_django() -> None:
    """Initialize Django settings if not already configured."""
    if not settings.configured:
        settings.configure(INSTALLED_APPS=PackageConfig.INSTALLED_APPS)


def setup_command_filtering() -> None:
    """
    Monkey-patch Django's get_commands to filter for tawala.scripts commands only.

    This ensures that only management commands from the tawala.scripts app are
    visible and executable through this CLI interface.
    """
    original_get_commands = management.get_commands

    def filtered_get_commands() -> Dict[str, str]:
        """Return only commands from tawala.scripts application."""
        commands = original_get_commands()
        return {name: app for name, app in commands.items() if app == "tawala.scripts"}

    management.get_commands = filtered_get_commands


def create_management_utility() -> ManagementUtility:
    """
    Create and configure the Django management utility.

    Returns:
        ManagementUtility: Configured utility with custom program name.
    """
    utility = ManagementUtility(sys.argv)
    utility.prog_name = "tawala"
    return utility


def main() -> None:
    """
    Main entry point for the Tawala CLI.

    This function orchestrates the setup and execution of the Django
    management utility with filtered commands.
    """
    # Set Django settings module
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", PackageConfig.SETTINGS_MODULE)

    # Initialize Django
    configure_django()

    # Setup command filtering
    setup_command_filtering()

    # Create and execute management utility
    utility = create_management_utility()
    utility.execute()


if __name__ == "__main__":
    main()
