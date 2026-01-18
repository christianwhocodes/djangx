#!/usr/bin/env python

import sys
from typing import NoReturn, Optional

from .. import PKG_NAME


def main() -> Optional[NoReturn]:
    """Main entry point for the CLI."""
    match sys.argv[1]:
        case "-v" | "--version" | "version":
            from christianwhocodes.utils.version import print_version

            sys.exit(print_version(PKG_NAME))

        case _:
            from os import environ
            from pathlib import Path

            from django.core.management import ManagementUtility

            sys.path.insert(0, str(Path.cwd()))
            environ.setdefault("DJANGO_SETTINGS_MODULE", f"{PKG_NAME}.settings")

            utility = ManagementUtility(sys.argv)
            utility.prog_name = PKG_NAME
            utility.execute()


if __name__ == "__main__":
    main()
