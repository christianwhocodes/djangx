"""Management command: run

Executes install or build commands.
Supports dry-run mode for previewing commands before execution
and continues running remaining commands even if one fails.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError, CommandParser

from ..art import ArtPrinter, ArtType


@dataclass
class CommandResult:
    """Result of executing a single command.

    Attributes:
        command: The command that was executed.
        success: Whether the command executed successfully.
        error: Error message if the command failed, None otherwise.
    """

    command: str
    success: bool
    error: str | None = None


class CommandOutput(ABC):
    """Base class for command process output handling.

    Defines the interface for displaying command process information,
    progress, and results. Subclasses can implement different output strategies.
    """

    def __init__(self, command: BaseCommand) -> None:
        """Initialize the output handler with a command reference.

        Args:
            command: The parent Command instance for stdout/styling.
        """
        self.command = command

    @abstractmethod
    def print_header(self, command_count: int, dry_run: bool, mode: str) -> None:
        """Print the command process header.

        Args:
            command_count: Number of commands to execute.
            dry_run: Whether running in dry-run mode.
            mode: The mode of operation (e.g., 'BUILD', 'INSTALL').
        """
        pass

    @abstractmethod
    def print_no_commands_error(self, mode: str) -> None:
        """Print error message when no commands are configured.

        Args:
            mode: The mode of operation (e.g., 'build', 'install').
        """
        pass

    @abstractmethod
    def print_dry_run_preview(self, commands: list[str]) -> None:
        """Print the dry-run preview of all commands.

        Args:
            commands: List of commands to preview.
        """
        pass

    @abstractmethod
    def print_command_header(self) -> None:
        """Print the command header before execution."""
        pass

    @abstractmethod
    def print_command_success(self, cmd: str, index: int, total: int) -> None:
        """Print successful command completion with progress bar.

        Args:
            cmd: The command that completed successfully.
            index: The current command index (1-based).
            total: The total number of commands.
        """
        pass

    @abstractmethod
    def print_command_failure(self, cmd: str, error: str, index: int, total: int) -> None:
        """Print command failure information with progress bar.

        Args:
            cmd: The command that failed.
            error: The error message.
            index: The current command index (1-based).
            total: The total number of commands.
        """
        pass

    @abstractmethod
    def print_summary(self, total: int, completed: int, failed: int) -> None:
        """Print the command process summary.

        Args:
            total: The total number of commands.
            completed: Number of successfully completed commands.
            failed: Number of failed commands.
        """
        pass


class CommandExecutor:
    """Executor for running commands.

    Handles parsing and execution of individual commands,
    including error handling and result tracking.
    """

    def __init__(self, command: BaseCommand) -> None:
        """Initialize the command executor.

        Args:
            command: The parent Command instance.
        """
        self.command = command

    def execute(self, cmd: str) -> CommandResult:
        """Execute a single command.

        Parses the command string, invokes the management command via call_command,
        and returns the result with any error information.

        Args:
            cmd: The command string to execute (e.g., 'collectstatic --noinput').

        Returns:
            CommandResult containing execution status and any error details.
        """
        try:
            # Validate and parse command
            parts: list[str] = cmd.strip().split()
            if not parts:
                return CommandResult(
                    command=cmd,
                    success=False,
                    error="Empty command string",
                )

            command_name: str = parts[0]
            command_args: list[str] = parts[1:]

            # Execute the management command
            call_command(command_name, *command_args)

            return CommandResult(command=cmd, success=True)
        except CommandError as e:
            return CommandResult(command=cmd, success=False, error=str(e))
        except (ValueError, OSError) as e:
            return CommandResult(command=cmd, success=False, error=str(e))


class CommandProcess:
    """Orchestrator for the command execution process.

    Coordinates command execution, output handling, and process flow.
    Manages the overall workflow including dry-run and actual execution.

    Attributes:
        command: The parent Command instance.
        output: The output handler for displaying information.
        executor: The command executor for running commands.
        mode: The mode of operation (e.g., 'BUILD', 'INSTALL').
    """

    def __init__(
        self,
        command: BaseCommand,
        output: CommandOutput,
        executor: CommandExecutor,
        mode: str,
    ) -> None:
        """Initialize the command process.

        Args:
            command: The parent Command instance.
            output: The output handler for displaying information.
            executor: The command executor for running commands.
            mode: The mode of operation (e.g., 'BUILD', 'INSTALL').
        """
        self.command = command
        self.output = output
        self.executor = executor
        self.mode = mode

    def run(self, commands: list[str], dry_run: bool = False) -> None:
        """Run the command process.

        Args:
            commands: List of commands to execute.
            dry_run: If True, show commands without executing them.
        """
        self.output.print_header(len(commands), dry_run, self.mode)

        if dry_run:
            self.output.print_dry_run_preview(commands)
            return

        self._execute_commands(commands)

    def _execute_commands(self, commands: list[str]) -> None:
        """Execute all commands sequentially.

        Args:
            commands: List of commands to execute.
        """
        total = len(commands)
        completed = 0
        failed = 0
        results: list[CommandResult] = []

        for i, cmd in enumerate(commands, 1):
            self.output.print_command_header()
            result = self.executor.execute(cmd)
            results.append(result)

            if result.success:
                self.output.print_command_success(cmd, i, total)
                completed += 1
            else:
                self.output.print_command_failure(cmd, result.error or "Unknown error", i, total)
                failed += 1

        self.output.print_summary(total, completed, failed)


class CommandGenerator(ABC):
    """Base generator for creating command execution processes.

    Provides a template for building management commands that execute
    a series of configured commands with consistent behavior.
    """

    def __init__(self, django_command: BaseCommand) -> None:
        """Initialize the command generator.

        Args:
            django_command: The Django BaseCommand instance.
        """
        self.django_command = django_command

    @abstractmethod
    def get_commands_from_settings(self) -> list[str]:
        """Retrieve commands from Django settings.

        Returns:
            List of command strings to execute.
        """
        pass

    @abstractmethod
    def create_output_handler(self) -> CommandOutput:
        """Create the output handler for the command process.

        Returns:
            An instance of CommandOutput for handling display.
        """
        pass

    @abstractmethod
    def get_mode(self) -> str:
        """Get the mode identifier for this command process.

        Returns:
            A string identifier like 'BUILD' or 'INSTALL'.
        """
        pass

    def generate(self, dry_run: bool = False) -> None:
        """Generate and execute the command process.

        Args:
            dry_run: If True, show commands without executing them.
        """
        commands = self.get_commands_from_settings()

        if not commands:
            output = self.create_output_handler()
            output.print_no_commands_error(self.get_mode().lower())
            return

        # Initialize components
        output = self.create_output_handler()
        executor = CommandExecutor(self.django_command)
        process = CommandProcess(self.django_command, output, executor, self.get_mode())

        # Run the process
        process.run(commands, dry_run=dry_run)


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
            self.command.style.SUCCESS(f"\n✨ Starting {display_mode.lower()} process...\n")
        )

        self.art_printer.print_run_process_banner(self.art_type, display_mode, command_count)

    def print_no_commands_error(self, mode: str) -> None:
        """Print error message when no commands are configured.

        Args:
            mode: The mode of operation (e.g., 'build', 'install').
        """
        self.command.stdout.write(self.command.style.ERROR(f"\n❌ No {mode} commands configured!"))
        self.command.stdout.write(
            self.command.style.WARNING(
                f"   Define {mode} commands in your '.env' file or in pyproject.toml [tool.{settings.PKG_NAME}] section:\n"
            )
        )
        self.command.stdout.write("")

    def print_dry_run_preview(self, commands: list[str]) -> None:
        """Print the dry-run preview of all commands.

        Args:
            commands: List of commands to preview.
        """
        self.command.stdout.write(self.command.style.NOTICE("Commands to be executed:\n"))

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

    def print_command_failure(self, cmd: str, error: str, index: int, total: int) -> None:
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
                self.command.style.SUCCESS(f"🎉 All {completed} command(s) completed successfully!")
            )
        else:
            self.command.stdout.write(
                self.command.style.SUCCESS(f"✓ {completed}/{total} command(s) completed")
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
        return settings.COMMANDS["BUILD"]

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
        return settings.COMMANDS["INSTALL"]

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
            self.stdout.write(self.style.ERROR("Please specify either 'install' or 'build'"))
            return None
