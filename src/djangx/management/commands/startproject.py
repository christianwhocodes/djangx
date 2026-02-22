"""Project initialization command."""

from christianwhocodes import ExitCode

# ============================================================================
# Public API
# ============================================================================


def handle_startproject() -> ExitCode:
    """Handle the ``startproject`` command.

    Returns:
        ExitCode.SUCCESS (0) or ExitCode.ERROR (1)

    """
    return ExitCode.SUCCESS
