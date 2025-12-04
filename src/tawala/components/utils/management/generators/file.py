import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List, TypedDict, cast

from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key

from .....conf import config
from .....conf.post import BASE_DIR, PKG_NAME


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


class RandomStringGenerator(FileGenerator):
    """Generator for random strings.

    Generates a cryptographically secure random string and optionally copies
    it to the system clipboard using pyperclip.

    Example:
        generator = RandomGenerator(command)
        generator.handle(no_clipboard=False)
    """

    def handle(self, *args: Any, **options: Any) -> None:
        """Generate and display a random string.

        Args:
            *args: Unused positional arguments.
            **options: Command options including:
                - no_clipboard (bool): If True, skip copying to clipboard.
        """
        random_str: str = get_random_secret_key()
        self.command.stdout.write(
            "Generated random string: " + self.command.style.SUCCESS(random_str)
        )

        if not options.get("no_clipboard", False):
            self._copy_to_clipboard(random_str)

    def _copy_to_clipboard(self, text: str) -> None:
        """Copy text to clipboard with error handling.

        Attempts to copy the given text to the system clipboard using pyperclip.
        Gracefully handles the case where pyperclip is not installed or copy fails.

        Args:
            text: The text to copy to the clipboard.
        """
        try:
            import pyperclip

            pyperclip.copy(text)
            self.command.stdout.write(
                self.command.style.SUCCESS("Copied to clipboard successfully.")
            )
        except ImportError:
            self.command.stdout.write(
                self.command.style.ERROR(
                    "pyperclip is not installed. Install it to enable clipboard functionality (uv add pyperclip)."
                )
            )
        except Exception as e:
            self.command.stdout.write(
                self.command.style.WARNING(f"Could not copy to clipboard: {e}")
            )


class RewriteRule(TypedDict):
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
        "rewrites": List[RewriteRule],
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
            json_text: str = json.dumps(content, indent=2)
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


class EnvFileGenerator(FileGenerator):
    """Generator for .env configuration file.

    Creates a .env file template at the project BASE_DIR with all available
    environment variables defined in config classes. Variables are commented
    out by default unless --uncomment is used.

    Example:
        generator = EnvGenerator(command)
        generator.handle(path=None, force=False, uncomment=False)

        # Generate with custom path
        generator.handle(path="/path/to/.env", force=True, uncomment=True)
    """

    def handle(self, *args: Any, **options: Any) -> None:
        """Generate or overwrite the .env configuration file.

        Args:
            *args: Unused positional arguments.
            **options: Command options including:
                - path (str|None): Custom path for the .env file.
                - force (bool): If True, overwrite existing files without prompting.
                - uncomment (bool): If True, leave variables uncommented (active).
        """

        # Determine the .env file path
        path_option = options.get("path")
        if path_option:
            env_path = Path(str(path_option))
        else:
            env_path: Path = Path(BASE_DIR) / ".env"

        # Check if file exists and handle accordingly
        if env_path.exists() and not options.get("force", False):
            if not self._prompt_overwrite(env_path):
                self.command.stdout.write(
                    self.command.style.WARNING("Aborted. .env file was not created.")
                )
                return

        # Generate the .env content
        uncomment = bool(options.get("uncomment", False))
        env_content = self._generate_env_content(uncomment=uncomment)

        # Write the file
        try:
            env_path.write_text(env_content, encoding="utf-8")
            self.command.stdout.write(
                self.command.style.SUCCESS(
                    f"Successfully created .env file at: {env_path}"
                )
            )
        except Exception as e:
            self.command.stdout.write(
                self.command.style.ERROR(f"Failed to write .env file: {e}")
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

    def _generate_env_content(self, uncomment: bool = False) -> str:
        """Generate the content for the .env file.

        Args:
            config: The config module containing configuration classes.
            uncomment: If True, variables will be uncommented (active).

        Returns:
            The complete .env file content as a string.
        """

        config_classes: list[tuple[str, type[config.BaseConfig]]] = [
            ("Security", config.SecurityConfig),
            ("Application", config.ApplicationConfig),
            ("Database", config.DatabaseConfig),
            ("Storage", config.StorageConfig),
            ("Commands", config.CommandsConfig),
        ]

        lines: list[str] = [
            "# ============================================================================",
            "# Environment Configuration",
            "# ============================================================================",
            "#",
            "# This file was auto-generated by the 'generate env' management command.",
            "# Uncomment and set the values you need for your environment.",
            "#",
            "",
        ]

        for section_name, config_class in config_classes:
            section_vars = config_class.get_env_var_info()

            if not section_vars:
                continue

            # Add section header
            header_lines: list[str] = [
                "",
                "# " + "=" * 76,
                f"# {section_name} Configuration",
                "# " + "=" * 76,
                "",
            ]
            lines.extend(header_lines)

            # Add each variable
            for var_info in section_vars:
                self._add_variable_lines(lines, var_info, uncomment)

        return "\n".join(lines) + "\n"

    def _add_variable_lines(
        self, lines: list[str], var_info: dict[str, Any], uncomment: bool
    ) -> None:
        """Add formatted lines for a single environment variable.

        Args:
            lines: The list to append lines to.
            var_info: Dictionary with variable information.
            uncomment: Whether to uncomment the variable.
        """
        env_key: str = str(var_info["env_key"])
        toml_key: Any = var_info["toml_key"]
        default: Any = var_info["default"]

        # Add description comment
        comment_parts: list[str] = []
        if toml_key:
            comment_parts.append(f"TOML: {toml_key}")
        if default is not None:
            comment_parts.append(f"Default: {default}")

        if comment_parts:
            lines.append(f"# {' | '.join(comment_parts)}")

        # Format the value
        value: str
        if default is not None:
            if isinstance(default, bool):
                value = str(default).lower()
            elif isinstance(default, list):
                # Cast to list[Any] to satisfy type checker
                default_list = cast(list[Any], default)
                value = ",".join(str(item) for item in default_list)
            else:
                value = str(default)
        else:
            value = ""

        # Add the variable line
        prefix = "" if uncomment else "# "
        lines.append(f"{prefix}{env_key}={value}")
        lines.append("")  # Empty line for spacing
