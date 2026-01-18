"""Management command: runbuild

Executes build commands.
Supports dry-run mode for previewing commands before execution
and continues running remaining commands even if one fails.
"""

from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from ..settings import RUNCOMMANDS
from ..helpers.art import ArtType
from ..helpers.run import CommandGenerator, CommandOutput, Output


class BuildCommandGenerator(CommandGenerator):
    """Generator for build command execution."""

    def get_runcommands(self) -> list[str]:
        """Retrieve build commands."""
        runcommands_conf = RUNCOMMANDS
        return runcommands_conf.build

    def create_output_handler(self) -> CommandOutput:
        """Create the output handler for build commands."""
        return Output(self.django_command, ArtType.BUILD)

    def get_mode(self) -> str:
        """Get the mode identifier for build commands."""
        return "BUILD"


class Command(BaseCommand):
    help = "Execute build commands"

    def add_arguments(self, parser: CommandParser) -> None:
        """Define command-line arguments.

        Args:
            parser: The argument parser to add arguments to.
        """
        parser.add_argument(
            "--dry",
            "--dry-run",
            dest="dry_run",
            action="store_true",
            help="Show commands that would be executed without running them",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Handle the runbuild command execution.

        Retrieves build commands, validates them,
        and either displays them (dry-run) or executes them sequentially.
        Continues execution even if individual commands fail.

        Args:
            *args: Unused positional arguments.
            **options: Command options including:
                - dry_run (bool): If True, show commands without executing.
        """
        dry_run: bool = options.get("dry_run", False)
        generator = BuildCommandGenerator(self)
        generator.generate(dry_run=dry_run)
