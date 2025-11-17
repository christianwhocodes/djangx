#!/usr/bin/env python
"""
Tawala CLI - Project Commands Executor.

This module provides the standard Django management interface for Tawala projects,
using the config.settings module when run from a user's project directory.
"""

import os
import sys
from pathlib import Path


class ProjectConfig:
    """Configuration for the Tawala management script."""

    SETTINGS_MODULE = "config.settings"
    PROG_NAME = "tawala"


def setup_python_path() -> None:
    """Add the current working directory to Python path for module imports."""
    sys.path.insert(0, str(Path.cwd()))


def configure_django_settings() -> None:
    """Set the Django settings module environment variable."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", ProjectConfig.SETTINGS_MODULE)


def create_management_utility():
    """
    Create and configure the Django management utility.

    Returns:
        ManagementUtility: Configured utility with custom program name.

    Raises:
        ImportError: If Django cannot be imported with troubleshooting guidance.
    """
    try:
        from django.core.management import ManagementUtility
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    utility = ManagementUtility(sys.argv)
    utility.prog_name = ProjectConfig.PROG_NAME
    return utility


def main() -> None:
    """
    Main entry point for the Tawala management script.

    This function orchestrates the setup and execution of Django's
    management utility for the Tawala project.
    """
    # Setup environment
    setup_python_path()
    configure_django_settings()

    # Create and execute management utility
    utility = create_management_utility()
    utility.execute()


if __name__ == "__main__":
    main()
