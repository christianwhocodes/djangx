"""CLI entry point."""

import sys

from christianwhocodes import ExitCode, InitAction, Text, cprint, print_version

from .. import PACKAGE, PROJECT, ProjectValidationError


def main() -> None:
    """Execute the CLI."""
    if len(sys.argv) < 2:
        cprint("No arguments passed.", Text.ERROR)
        sys.exit(ExitCode.ERROR)

    match sys.argv[1]:
        case "-v" | "--version" | "version":
            sys.exit(print_version(PACKAGE.name))

        case command if command in InitAction:
            from .commands.startproject import Command

            sys.exit(Command()(sys.argv[2:]))

        case _:
            try:
                PROJECT.validate()
            except ProjectValidationError as e:
                cprint(f"Is this a valid {PACKAGE.display_name} project directory?\n{e}", Text.WARNING)
                cprint(
                    f"Assuming you have uv installed:\n"
                    f"    - run: 'uvx {PACKAGE.name} {InitAction.STARTPROJECT.value} <project_name>' to initialize a new project.\n"
                    f"    - run: 'uvx {PACKAGE.name} {InitAction.STARTPROJECT.value} -h' to see help on the command.",
                    Text.INFO,
                )
                sys.exit(ExitCode.ERROR)
            except Exception as e:
                cprint(f"Unexpected error during project validation:\n{e}", Text.ERROR)
                sys.exit(ExitCode.ERROR)
            else:
                from os import environ

                from django.core.management import ManagementUtility

                sys.path.insert(0, str(PROJECT.base_dir))
                environ.setdefault("DJANGO_SETTINGS_MODULE", PACKAGE.settings_module)

                utility = ManagementUtility(sys.argv)
                utility.prog_name = PACKAGE.name
                utility.execute()


if __name__ == "__main__":
    main()
