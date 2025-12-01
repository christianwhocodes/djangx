#!/usr/bin/env python
"""
Tawala CLI.

Provides the management commands interface for Tawala.
"""

import os
import sys

from django.core.management import ManagementUtility

from .conf.management.path import BasePath


def main() -> None:
    """Main entry point for the Tawala CLI."""

    base_dir = BasePath.get_base_dir_or_exit()
    sys.path.insert(0, str(base_dir))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tawala.conf.settings")

    utility = ManagementUtility(sys.argv)
    utility.prog_name = "tawala"
    utility.execute()


if __name__ == "__main__":
    main()
