from abc import ABC, abstractmethod
from json import dumps
from pathlib import Path
from typing import Any, TypedDict, cast

from django.core.management.base import BaseCommand, CommandParser

from .....core.app.postsettings import BASE_DIR, PKG_NAME


class FileGenerator(ABC):
    """Base class for generators.

    Defines the interface for all generator types. Subclasses must implement
    the handle method to define their specific generation logic.

    Attributes:
        command: Reference to the parent Command instance for output and styling.
    """

    def __init__(self, command: "BaseCommand") -> None:
        """Initialize the generator with a command reference.

        Args:
            command: The parent Command instance.
        """
        self.command = command

    @abstractmethod
    def handle(self, *args: Any, **options: Any) -> None:
        """Execute the generator logic.

        Args:
            *args: Positional arguments passed from the command.
            **options: Keyword arguments passed from the command, containing
                parsed command-line options.
        """
        pass


class VercelJSONRewrites(TypedDict):
    """TypedDict for URL rewrite rules in Vercel configuration.

    Attributes:
        source: The source URL pattern.
        destination: The destination URL pattern.
    """

    source: str
    destination: str


VercelConfig = TypedDict(
    "VercelConfig",
    {
        "$schema": str,
        "installCommand": str,
        "buildCommand": str,
        "rewrites": list[VercelJSONRewrites],
    },
)


class VercelJSONFileGenerator(FileGenerator):
    """Generator for Vercel configuration file.

    Creates a vercel.json configuration file at the project BASE_DIR with
    appropriate build commands and URL rewrites for the ASGI application.
    Prompts for confirmation if the file already exists, unless --force is used.

    Example:
        generator = VercelGenerator(command)
        generator.handle(force=False)

        # With force flag to overwrite without prompting
        generator.handle(force=True)
    """

    def handle(self, *args: Any, **options: Any) -> None:
        """Generate or overwrite the Vercel configuration file.

        Args:
            *args: Unused positional arguments.
            **options: Command options including:
                - force (bool): If True, overwrite existing files without prompting.
        """
        vercel_path = BASE_DIR / "vercel.json"

        # Check if file exists and handle accordingly
        if vercel_path.exists() and not options.get("force", False):
            if not self._prompt_overwrite(vercel_path):
                self.command.stdout.write(
                    self.command.style.WARNING(
                        "Aborted. vercel.json was not overwritten."
                    )
                )
                return

        content: VercelConfig = {
            "$schema": "https://openapi.vercel.sh/vercel.json",
            "installCommand": f"uv run {PKG_NAME} run install",
            "buildCommand": f"uv run {PKG_NAME} run build",
            "rewrites": [{"source": "/(.*)", "destination": "/api/asgi"}],
        }

        try:
            json_text: str = dumps(content, indent=2)
            vercel_path.write_text(json_text, encoding="utf-8")

            self.command.stdout.write(
                self.command.style.SUCCESS(f"vercel.json created at: {vercel_path}")
            )
        except Exception as exc:
            self.command.stdout.write(
                self.command.style.ERROR(f"Failed to create vercel.json: {exc}")
            )

    def _prompt_overwrite(self, file_path: Path) -> bool:
        """Prompt user for confirmation to overwrite existing file.

        Args:
            file_path: The path to the existing file.

        Returns:
            True if the user enters 'y' or 'Y', False otherwise (defaults to no).
        """
        prompt: str = (
            f"\n{self.command.style.WARNING(str(file_path))} already exists. "
            f"Overwrite? [y/N]: "
        )
        response: str = input(prompt).strip().lower()
        return response == "y"


class Command(BaseCommand):
    help = "Generate various project configuration files."
    requires_system_checks: bool = cast(bool, [])

    GENERATORS: dict[str, type[FileGenerator]] = {
        "vercel": VercelJSONFileGenerator,
    }

    def add_arguments(self, parser: CommandParser) -> None:
        """Define command-line arguments.

        Args:
            parser: The argument parser to add arguments to.
        """
        parser.add_argument(
            "file",
            type=str,
            choices=self.GENERATORS.keys(),
            help="Specify which file to create",
        )

        parser.add_argument(
            "-f",
            "--force",
            "--overwrite",
            dest="force",
            action="store_true",
            help="Overwrite existing files without prompting",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        generator_name: str = options["generator"]

        generator_class = self.GENERATORS[generator_name]
        generator: FileGenerator = generator_class(self)
        generator.handle(*args, **options)
