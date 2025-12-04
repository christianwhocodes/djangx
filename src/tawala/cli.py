#!/usr/bin/env python
import os
import sys
from typing import NoReturn, Optional

from christianwhocodes.helpers import ExitCode, version_placeholder
from django.core.management import ManagementUtility

from .conf.pre import PKG, PROJECT


def main() -> Optional[NoReturn]:
    f"""Main entry point for the {PKG.name.capitalize()} CLI."""

    match sys.argv[1]:
        case "-v" | "--version" | "version":
            version = PKG.get_version()

            if version != version_placeholder():
                print(version)
                sys.exit(ExitCode.SUCCESS)
            else:
                print(f"Could not determine {PKG.name} version.")
                sys.exit(ExitCode.ERROR)

        case _:
            base_dir = PROJECT.get_base_dir_or_exit()
            sys.path.insert(0, str(base_dir))
            os.environ.setdefault(
                "DJANGO_SETTINGS_MODULE", f"{PKG.name}.conf.settings"
            )

            utility = ManagementUtility(sys.argv)
            utility.prog_name = PKG.name
            utility.execute()


if __name__ == "__main__":
    main()
