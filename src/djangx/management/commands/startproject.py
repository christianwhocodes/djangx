"""Project initialization command."""

from argparse import ArgumentParser, Namespace

from christianwhocodes import ExitCode, InitAction

from ... import PACKAGE

# ============================================================================
# Public API
# ============================================================================


def handle_startproject(argv: list[str]) -> ExitCode:
    """Handle the ``startproject`` command.

    Returns:
        ExitCode.SUCCESS (0) or ExitCode.ERROR (1)

    """
    actions = " | ".join(InitAction)
    parser = ArgumentParser(
        prog=f"{PACKAGE.name} [{actions}] <project_name>",
        description=f"Initialize a new {PACKAGE.display_name} project.",
    )
    _: Namespace = parser.parse_args(argv)
    return ExitCode.SUCCESS
