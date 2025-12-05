#!/usr/bin/env python

from os import environ
from sys import argv, exit, path
from typing import NoReturn, Optional

from christianwhocodes.helpers import ExitCode, Version
from christianwhocodes.stdout import print
from django.core.management import ManagementUtility

from .. import PKG, PROJECT


def main() -> Optional[NoReturn]:
    f"""Main entry point for the {PKG.name.capitalize()} CLI."""

    match argv[1]:
        case "-v" | "--version" | "version":
            if PKG.version != Version.placeholder():
                print(PKG.version)
                exit(ExitCode.SUCCESS)
            else:
                print(f"{PKG.version}: Could not determine {PKG.name} version.")
                exit(ExitCode.ERROR)

        case _:
            path.insert(0, str(PROJECT.base_dir))
            environ.setdefault(
                "DJANGO_SETTINGS_MODULE", f"{PKG.name}.core.app.settings"
            )

            utility = ManagementUtility(argv)
            utility.prog_name = PKG.name
            utility.execute()


if __name__ == "__main__":
    main()
