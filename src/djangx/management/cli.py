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
            from .commands import StartprojectCommand

            sys.exit(StartprojectCommand()(sys.argv[2:]))

        case _:
            try:
                PROJECT.validate()
            except ProjectValidationError as e:
                cprint(f"Not in a valid {PACKAGE.display_name} project directory: {e}", Text.WARNING)
                actions = " | ".join(InitAction)
                cprint(
                    f"Use '{PACKAGE.name} [{actions}] <project_name>' to initialize a new project.",
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
