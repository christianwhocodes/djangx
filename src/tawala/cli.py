"""
Command-line interface for Tawala.
Handles routing commands to appropriate scripts based on execution context.
"""

import subprocess
import sys
from pathlib import Path
from typing import NoReturn


class TawalaPaths:
    """Centralized path management for Tawala CLI."""

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.scripts_dir = self.base_dir / "scripts"
        self.commands_dir = self.base_dir / "utils" / "management" / "commands"

    @property
    def package_script(self) -> Path:
        """Script for executing commands from package directory."""
        return self.scripts_dir / "execute_from_package_dir.py"

    @property
    def project_script(self) -> Path:
        """Script for executing commands from project directory."""
        return self.scripts_dir / "execute_from_project_dir.py"


class ExecutionContext:
    """Determines the execution context of the CLI."""

    @staticmethod
    def is_in_package_dir() -> bool:
        """
        Check if executed from Tawala package directory.

        Returns:
            bool: True if in package directory (no config/settings.py),
                  False if in user project directory.
        """
        config_file = Path.cwd() / "config" / "settings.py"
        return not config_file.exists()

    @staticmethod
    def is_in_project_dir() -> bool:
        """Check if executed from user project directory."""
        return not ExecutionContext.is_in_package_dir()


class CommandRegistry:
    """Manages available Tawala commands."""

    def __init__(self, paths: TawalaPaths):
        self.paths = paths

    def get_available_commands(self) -> list[str]:
        """
        Get list of available Tawala-specific commands.

        Returns:
            list[str]: Command names available in the commands directory.
                       Includes 'help' when in package directory.
        """
        commands = [
            f.stem for f in self.paths.commands_dir.glob("*.py") if f.stem != "__init__"
        ]

        if ExecutionContext.is_in_package_dir():
            commands.append("help")

        return commands

    def is_package_command(self, command: str) -> bool:
        """Check if command is a Tawala-specific command."""
        return command in self.get_available_commands()


class CommandExecutor:
    """Executes commands in appropriate context."""

    def __init__(self, paths: TawalaPaths):
        self.paths = paths

    def execute_package_command(self, command: str, args: list[str]) -> NoReturn:
        """
        Execute a Tawala-specific command from package directory.

        Args:
            command: The command to execute
            args: Additional command-line arguments
        """
        result = subprocess.run(
            [sys.executable, str(self.paths.package_script), command] + args
        )
        sys.exit(result.returncode)

    def execute_project_command(self, args: list[str]) -> NoReturn:
        """
        Execute a Django command from user project directory.

        Args:
            args: Complete command-line arguments
        """
        result = subprocess.run([sys.executable, str(self.paths.project_script)] + args)
        sys.exit(result.returncode)


class TawalaCLI:
    """Main CLI orchestrator for Tawala."""

    def __init__(self):
        self.paths = TawalaPaths()
        self.registry = CommandRegistry(self.paths)
        self.executor = CommandExecutor(self.paths)

    def show_error(self, message: str) -> NoReturn:
        """Display error message and exit."""
        print(message)
        sys.exit(1)

    def route_command(self, command: str, args: list[str]) -> NoReturn:
        """
        Route command to appropriate execution context.

        Args:
            command: The command to execute
            args: Additional command-line arguments
        """
        # Handle Tawala-specific commands
        if self.registry.is_package_command(command):
            self.executor.execute_package_command(command, args)

        # Handle Django commands in project directory
        if ExecutionContext.is_in_project_dir():
            self.executor.execute_project_command([command] + args)

        # Unknown command in package directory
        self.show_error(
            (
                f"Unknown command: '{command}'"
                "\nType 'tawala help' for usage."
                "\n\n\033[1;93mIf this is a Django command and you have initialised a project, "
                "please run it from your Tawala project directory.\033[0m"
            )
        )

    def run(self) -> NoReturn:
        """Main entry point for CLI execution."""
        if len(sys.argv) < 2:
            self.show_error("No command provided.")

        try:
            command = sys.argv[1]
            args = sys.argv[2:]
            self.route_command(command, args)
        except KeyboardInterrupt:
            sys.exit(1)


def main() -> None:
    """Entry point for the Tawala CLI."""
    cli = TawalaCLI()
    cli.run()


if __name__ == "__main__":
    main()
