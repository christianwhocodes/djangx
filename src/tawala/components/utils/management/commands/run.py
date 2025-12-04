"""Management command: run

Executes install or build commands.
Supports dry-run mode for previewing commands before execution
and continues running remaining commands even if one fails.
"""

from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from .....conf.post import COMMANDS_BUILD, COMMANDS_INSTALL, PKG_NAME
from ..art import ArtPrinter, ArtType
from ..generators.command import CommandGenerator, CommandOutput


class Output(CommandOutput):
    """Command process output with ASCII art and emojis.

    Provides colorful, visually appealing output with progress bars,
    ASCII art, and strategic use of emojis and colors.
    """

    def __init__(self, command: BaseCommand, art_type: ArtType) -> None:
        """Initialize the output handler.

        Args:
            command: The parent Command instance for stdout/styling.
            art_type: The type of ASCII art for this command.
        """
        super().__init__(command)
        self.art_type = art_type
        self.art_printer = ArtPrinter(command)

    def print_header(self, command_count: int, dry_run: bool, mode: str) -> None:
        """Print the command process header with ASCII art.

        Args:
            command_count: Number of commands to execute.
            dry_run: Whether running in dry-run mode.
            mode: The mode of operation (e.g., 'BUILD', 'INSTALL').
        """
        display_mode = "DRY RUN" if dry_run else mode

        self.command.stdout.write(
            self.command.style.SUCCESS(
                f"\n✨ Starting {display_mode.lower()} process...\n"
            )
        )

        self.art_printer.print_run_process_banner(
            self.art_type, display_mode, command_count
        )

    def print_no_commands_error(self, mode: str) -> None:
        """Print error message when no commands are configured.

        Args:
            mode: The mode of operation (e.g., 'build', 'install').
        """
        self.command.stdout.write(
            self.command.style.ERROR(f"\n❌ No {mode} commands configured!")
        )
        self.command.stdout.write(
            self.command.style.WARNING(
                f"   Define {mode} commands in your '.env' file or in pyproject.toml [tool.{PKG_NAME}] section:\n"
            )
        )
        self.command.stdout.write("")

    def print_dry_run_preview(self, commands: list[str]) -> None:
        """Print the dry-run preview of all commands.

        Args:
            commands: List of commands to preview.
        """
        self.command.stdout.write(
            self.command.style.NOTICE("Commands to be executed:\n")
        )

        for i, cmd in enumerate(commands, 1):
            self.command.stdout.write(
                f"  {self.command.style.NOTICE(f'[{i}]')} {self.command.style.HTTP_INFO(cmd)}"
            )

        self.command.stdout.write("")
        self.command.stdout.write(
            self.command.style.HTTP_NOT_MODIFIED(
                "✨ Remove --dry-run flag to execute these commands"
            )
        )
        self.command.stdout.write("")

    def print_command_header(self) -> None:
        """Print the command header before execution."""
        self.command.stdout.write(self.command.style.HTTP_NOT_MODIFIED("=" * 60 + "\n"))

    def print_command_success(self, cmd: str, index: int, total: int) -> None:
        """Print successful command completion with progress bar.

        Args:
            cmd: The command that completed successfully.
            index: The current command index (1-based).
            total: The total number of commands.
        """
        progress_bar = self._create_progress_bar(index, total)
        self.command.stdout.write(f"\n{progress_bar}")
        self.command.stdout.write(self.command.style.SUCCESS(f"✓ Completed: {cmd}"))
        self.command.stdout.write("")

    def print_command_failure(
        self, cmd: str, error: str, index: int, total: int
    ) -> None:
        """Print command failure information with progress bar.

        Args:
            cmd: The command that failed.
            error: The error message.
            index: The current command index (1-based).
            total: The total number of commands.
        """
        progress_bar = self._create_progress_bar(index, total)
        self.command.stdout.write(f"\n{progress_bar}")
        self.command.stdout.write(self.command.style.ERROR(f"✗ Failed: {cmd}"))
        self.command.stdout.write(self.command.style.ERROR(f"   Error: {error}"))
        self.command.stdout.write("")

    def print_summary(self, total: int, completed: int, failed: int) -> None:
        """Print the command process summary.

        Args:
            total: The total number of commands.
            completed: Number of successfully completed commands.
            failed: Number of failed commands.
        """
        self.command.stdout.write(self.command.style.HTTP_NOT_MODIFIED("=" * 60 + "\n"))
        if failed == 0:
            self.command.stdout.write(
                self.command.style.SUCCESS(
                    f"🎉 All {completed} command(s) completed successfully!"
                )
            )
        else:
            self.command.stdout.write(
                self.command.style.SUCCESS(
                    f"✓ {completed}/{total} command(s) completed"
                )
            )
            self.command.stdout.write(
                self.command.style.ERROR(f"✗ {failed}/{total} command(s) failed")
            )

        self.command.stdout.write("")

    def _create_progress_bar(self, current: int, total: int) -> str:
        """Create a visual progress bar for the commands.

        Args:
            current: The current command index (1-based).
            total: The total number of commands.

        Returns:
            A formatted progress bar string.
        """
        bar_length = 40
        filled = int(bar_length * current / total)
        bar = "█" * filled + "░" * (bar_length - filled)
        percentage = (current / total) * 100

        return (
            f"  [{bar}] "
            f"{self.command.style.HTTP_INFO(f'{current}/{total}')} "
            f"({self.command.style.NOTICE(f'{percentage:.0f}%')})"
        )


class BuildCommandGenerator(CommandGenerator):
    """Generator for build command execution."""

    def get_commands_from_settings(self) -> list[str]:
        """Retrieve build commands."""
        return COMMANDS_BUILD

    def create_output_handler(self) -> CommandOutput:
        """Create the output handler for build commands."""
        return Output(self.django_command, ArtType.BUILD)

    def get_mode(self) -> str:
        """Get the mode identifier for build commands."""
        return "BUILD"


class InstallCommandGenerator(CommandGenerator):
    """Generator for install command execution."""

    def get_commands_from_settings(self) -> list[str]:
        """Retrieve install commands."""
        return COMMANDS_INSTALL

    def create_output_handler(self) -> CommandOutput:
        """Create the output handler for install commands."""
        return Output(self.django_command, ArtType.INSTALL)

    def get_mode(self) -> str:
        """Get the mode identifier for install commands."""
        return "INSTALL"


class Command(BaseCommand):
    help = "Execute install or build commands"

    def add_arguments(self, parser: CommandParser) -> None:
        """Define command-line arguments.

        Args:
            parser: The argument parser to add arguments to.
        """
        # Create mutually exclusive group for command type
        group = parser.add_mutually_exclusive_group(required=True)

        # Positional arguments
        group.add_argument(
            "command_type",
            nargs="?",
            choices=["install", "build"],
            help="Type of commands to execute (install or build)",
        )

        # Optional flag arguments
        group.add_argument(
            "-i",
            "--install",
            action="store_true",
            help="Execute install commands",
        )

        group.add_argument(
            "-b",
            "--build",
            action="store_true",
            help="Execute build commands",
        )

        # Dry-run option
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show commands that would be executed without running them",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Handle the run command execution.

        Retrieves install or build commands, validates them,
        and either displays them (dry-run) or executes them sequentially.
        Continues execution even if individual commands fail.

        Args:
            *args: Unused positional arguments.
            **options: Command options including:
                - command_type (str): Either 'install' or 'build'.
                - install (bool): If True, execute install commands.
                - build (bool): If True, execute build commands.
                - dry_run (bool): If True, show commands without executing.
        """
        dry_run: bool = options.get("dry_run", False)
        generator = self._get_generator(options)

        if generator:
            generator.generate(dry_run=dry_run)

    def _get_generator(self, options: dict[str, Any]) -> CommandGenerator | None:
        """Get the appropriate command generator based on options.

        Args:
            options: Command options dictionary.

        Returns:
            The appropriate CommandGenerator instance, or None if invalid options.
        """
        command_type = options.get("command_type")
        is_install = options.get("install", False)
        is_build = options.get("build", False)

        if command_type == "install" or is_install:
            return InstallCommandGenerator(self)
        elif command_type == "build" or is_build:
            return BuildCommandGenerator(self)
        else:
            self.stdout.write(
                self.style.ERROR("Please specify either 'install' or 'build'")
            )
            return None
