"""Management command: copy

Copies files or folders with their contents from one location to another.
Automatically detects the source type and handles both file and directory
copying with appropriate error handling and user prompts.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from shutil import copy2, copytree, rmtree
from typing import Any, cast

from django.core.management.base import BaseCommand, CommandParser


class Copier(ABC):
    """Base class for copy operations.

    This abstract class defines the interface for copying files or directories.
    Subclasses must implement the copy method for specific copy strategies.

    Attributes:
        command: Reference to the parent Command instance for output and styling.
    """

    def __init__(self, command: "Command") -> None:
        """Initialize the copier with a command reference.

        Args:
            command: The parent Command instance.
        """
        self.command = command

    @abstractmethod
    def copy(self, source: Path, destination: Path) -> bool:
        """Execute the copy operation.

        Args:
            source: Source path to copy from.
            destination: Destination path to copy to.

        Returns:
            True if the copy operation was successful, False otherwise.
        """
        pass

    def _validate_source(self, source: Path) -> bool:
        """Validate that source exists and is accessible.

        Args:
            source: The source path to validate.

        Returns:
            True if source exists and is valid, False otherwise.
        """
        if not source.exists():
            self.command.stdout.write(
                self.command.style.ERROR(f"Source path does not exist: {source}")
            )
            return False
        return True


class FileCopier(Copier):
    """Copier for individual files.

    Handles copying of single files while preserving metadata and creating
    necessary parent directories at the destination.

    Example:
        copier = FileCopier(command)
        copier.copy(Path("source.txt"), Path("dest/source.txt"))
    """

    def copy(self, source: Path, destination: Path) -> bool:
        """Copy a single file.

        Preserves file metadata and creates parent directories as needed.
        Uses shutil.copy2 for metadata preservation.

        Args:
            source: Path to the source file.
            destination: Path where the file should be copied to.

        Returns:
            True if the file was copied successfully, False otherwise.
        """
        if not self._validate_source(source):
            return False

        if not source.is_file():
            self.command.stdout.write(self.command.style.ERROR(f"Source is not a file: {source}"))
            return False

        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            copy2(source, destination)
            self.command.stdout.write(
                self.command.style.SUCCESS(
                    f"File copied successfully from {source} to {destination}"
                )
            )
            return True
        except PermissionError:
            self.command.stdout.write(
                self.command.style.ERROR(
                    "Permission denied. Check read/write permissions for source and destination."
                )
            )
            return False
        except Exception as e:
            self.command.stdout.write(
                self.command.style.ERROR(f"Failed to copy file: {type(e).__name__}: {e}")
            )
            return False


class DirectoryCopier(Copier):
    """Copier for directories with all their contents.

    Recursively copies entire directory structures while preserving the
    directory hierarchy. Prompts for confirmation if the destination already
    exists, allowing the user to abort or proceed with overwriting.

    Example:
        copier = DirectoryCopier(command)
        copier.copy(Path("source_dir/"), Path("dest_dir/"))
    """

    def copy(self, source: Path, destination: Path) -> bool:
        """Copy a directory with all its contents.

        Recursively copies the source directory to the destination. If the
        destination already exists, prompts the user for confirmation before
        proceeding. Uses shutil.copytree for recursive copying.

        Args:
            source: Path to the source directory.
            destination: Path where the directory should be copied to.

        Returns:
            True if the directory was copied successfully, False otherwise.
        """
        if not self._validate_source(source):
            return False

        if not source.is_dir():
            self.command.stdout.write(
                self.command.style.ERROR(f"Source is not a directory: {source}")
            )
            return False

        try:
            if destination.exists():
                if not self._prompt_overwrite(destination):
                    self.command.stdout.write(self.command.style.WARNING("Copy aborted."))
                    return False
                rmtree(destination)

            copytree(source, destination, dirs_exist_ok=False)
            self.command.stdout.write(
                self.command.style.SUCCESS(
                    f"Directory copied successfully from {source} to {destination}"
                )
            )
            return True
        except PermissionError:
            self.command.stdout.write(
                self.command.style.ERROR(
                    "Permission denied. Check read/write permissions for source and destination."
                )
            )
            return False
        except Exception as e:
            self.command.stdout.write(
                self.command.style.ERROR(f"Failed to copy directory: {type(e).__name__}: {e}")
            )
            return False

    def _prompt_overwrite(self, destination: Path) -> bool:
        """Prompt user for confirmation to overwrite existing directory.

        Args:
            destination: The path to the existing directory.

        Returns:
            True if the user enters 'y' or 'Y', False otherwise (defaults to no).
        """
        prompt: str = (
            f"\n{self.command.style.WARNING(str(destination))} already exists. Overwrite? [y/N]: "
        )
        response: str = input(prompt).strip().lower()
        return response == "y"


class Command(BaseCommand):
    help = "Copy files or folders with their contents from one location to another."
    requires_system_checks: bool = cast(bool, [])

    def add_arguments(self, parser: CommandParser) -> None:
        """Define command-line arguments.

        Supports multiple aliases for source and destination paths for convenience.

        Args:
            parser: The argument parser to add arguments to.
        """
        parser.add_argument(
            "-i",
            "--input",
            "--source",
            dest="source",
            type=str,
            required=True,
            help="Source file or folder path to copy from",
        )
        parser.add_argument(
            "-o",
            "--output",
            "--destination",
            dest="destination",
            type=str,
            required=True,
            help="Destination file or folder path to copy to",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Handle the copy command execution.

        Automatically detects whether the source is a file or directory
        and uses the appropriate copier. Can be called via call_command
        in other management commands for programmatic use.

        Args:
            *args: Unused positional arguments.
            **options: Command options including:
                - source (str): The source file or directory path.
                - destination (str): The destination file or directory path.

        Example:
            from django.core.management import call_command
            call_command('copy', source='templates/', destination='project/templates/')
            call_command('copy', source='config.json', destination='backup/config.json')
        """
        source_str: str = options["source"]
        destination_str: str = options["destination"]

        source: Path = Path(source_str).resolve()
        destination: Path = Path(destination_str).resolve()

        # Determine copier based on source type
        if source.is_file():
            copier: Copier = FileCopier(self)
        elif source.is_dir():
            copier = DirectoryCopier(self)
        else:
            self.stdout.write(
                self.style.ERROR(f"Source is neither a file nor a directory: {source}")
            )
            return

        copier.copy(source, destination)
