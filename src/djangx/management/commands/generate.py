import builtins
import pathlib
from enum import StrEnum
from typing import Any, Optional, Type, cast

from christianwhocodes.generators import (
    FileGenerator,
    FileGeneratorOption,
    PgPassFileGenerator,
    PgServiceFileGenerator,
    SSHConfigFileGenerator,
)
from django.core.management.base import BaseCommand, CommandParser

from ... import PKG_DISPLAY_NAME, PKG_NAME, Conf
from ..settings import FILE_GENERATOR_PATHS, RUNCOMMANDS


class FileOption(StrEnum):
    PG_SERVICE = FileGeneratorOption.PG_SERVICE.value
    PGPASS = FileGeneratorOption.PGPASS.value
    SSH_CONFIG = FileGeneratorOption.SSH_CONFIG.value
    ENV = "env"
    SERVER = "server"
    VERCEL = "vercel"


class EnvFileGenerator(FileGenerator):
    """
    Generator for environment configuration file (.env.example).

    Creates a .env.example file in the base directory with all
    possible environment variables from configuration classes.
    All variables are commented out by default.
    """

    @property
    def file_path(self) -> pathlib.Path:
        """Return the path for the .env.example file."""
        paths_config = FILE_GENERATOR_PATHS
        return paths_config.dotenv_example

    @property
    def data(self) -> str:
        """Generate .env file content based on all ConfFields from Conf subclasses."""

        lines: list[str] = []

        # Add header
        lines.extend(self._add_header())

        # Get all fields from Conf subclasses
        env_fields = Conf.get_env_fields()

        # Group fields by class
        fields_by_class: dict[str, list[dict[str, Any]]] = {}
        for field in env_fields:
            class_name = cast(str, field["class"])
            if class_name not in fields_by_class:
                fields_by_class[class_name] = []
            fields_by_class[class_name].append(field)

        # Generate content for each class group
        for class_name in sorted(fields_by_class.keys()):
            fields = fields_by_class[class_name]

            # Add section header
            lines.extend(self._add_section_header(class_name))

            # Process each field in this class
            for field in fields:
                env_var = field["env"]
                toml_key = field["toml"]
                choices_key = field["choices"]
                default_value = field["default"]
                field_type = field["type"]

                # Add field documentation with proper format hints
                lines.append(
                    f"# Variable: {self._format_variable_hint(env_var, choices_key, field_type)}"
                )
                if toml_key:
                    lines.append(f"# TOML Key: {toml_key}")

                # Format default value for display
                if default_value is not None:
                    formatted_default = self._format_default_value(default_value, field_type)
                    lines.append(f"# Default: {formatted_default}")
                else:
                    lines.append("# Default: (none)")

                lines.append(f"# {env_var}=")

                lines.append("")

            lines.append("")

        # Add footer
        lines.extend(self._add_footer())

        return "\n".join(lines)

    def _add_header(self) -> list[str]:
        """Add header to the .env.example file."""
        lines: list[str] = []
        lines.append("# " + "=" * 78)
        lines.append(f"# {PKG_DISPLAY_NAME} Environment Configuration")
        lines.append("# " + "=" * 78)
        lines.append("#")
        lines.append("# This file contains all available environment variables for configuration.")
        lines.append("#")
        lines.append("# Configuration Priority: ENV > TOML > Default")
        lines.append("# " + "=" * 78)
        lines.append("")
        return lines

    def _add_section_header(self, class_name: str) -> list[str]:
        """Add section header for a configuration class."""
        lines: list[str] = []
        lines.append("# " + "-" * 78)
        lines.append(f"# {class_name} Configuration")
        lines.append("# " + "-" * 78)
        lines.append("")
        return lines

    def _add_footer(self) -> list[str]:
        """Add footer to the .env.example file."""
        lines: list[str] = []
        lines.append("# " + "=" * 78)
        lines.append("# End of Configuration")
        lines.append("# " + "=" * 78)
        return lines

    def _format_choices(self, choices: list[str]) -> str:
        """Format choices as 'choice1' | 'choice2' | 'choice3'."""
        return " | ".join(f'"{choice}"' for choice in choices)

    def _get_type_example(self, field_type: type) -> str:
        """Get example value for a field type."""
        match field_type:
            case builtins.bool:
                return '"true" | "false"'
            case builtins.int:
                return '"123"'
            case builtins.float:
                return '"123.45"'
            case builtins.list:
                return '"value1,value2,value3"'
            case pathlib.Path:
                return '"/full/path/to/something"'
            case _:
                return '"value"'

    def _format_variable_hint(
        self, env_var: str, choices_key: Optional[list[str]], field_type: type
    ) -> str:
        """Format variable hint showing proper syntax based on type."""
        if choices_key:
            return f"{env_var}={self._format_choices(choices_key)}"
        else:
            return f"{env_var}={self._get_type_example(field_type)}"

    def _format_default_value(self, value: Any, field_type: type) -> str:
        """Format default value for display in comments."""
        if value is None:
            return "(none)"

        match field_type:
            case builtins.bool:
                return "true" if value else "false"
            case builtins.list:
                if isinstance(value, list):
                    list_items = cast(list[Any], value)
                    if not list_items:
                        return "(empty list)"
                    return ",".join(str(v) for v in list_items)
                return str(value)
            case pathlib.Path:
                return str(pathlib.PurePosixPath(value))
            case _:
                return str(value)


class ServerFileGenerator(FileGenerator):
    f"""
    Generator for ASGI / WSGI configuration in api/server.py file.
    
    Creates an server.py file in the /api directory.
    Required for running {PKG_DISPLAY_NAME} apps with ASGI or WSGI servers.
    Note that the type of api gateway dependes on the SERVER_USE_ASGI setting.
    """

    @property
    def file_path(self) -> pathlib.Path:
        """Return the path for the api/server.py"""
        return FILE_GENERATOR_PATHS.server_py

    @property
    def data(self) -> str:
        """Return template content for api/server.py."""
        return f"from {PKG_NAME}.api.backends.server import application\n\napp = application\n"


class VercelFileGenerator(FileGenerator):
    """
    Generator for Vercel configuration file (vercel.json).

    Creates a vercel.json file in the base directory.
    Useful for deploying to Vercel with custom install/build commands.
    """

    @property
    def file_path(self) -> pathlib.Path:
        """Return the path for the vercel.json."""
        paths_config = FILE_GENERATOR_PATHS
        return paths_config.vercel_json

    @property
    def data(self) -> str:
        """Return template content for vercel.json."""
        lines = [
            "{",
            '  "$schema": "https://openapi.vercel.sh/vercel.json",',
        ]

        # Add installCommand only if RUNCOMMANDS.install is non-empty
        if RUNCOMMANDS.install:
            lines.append(f'  "installCommand": "uv run {PKG_NAME} runinstall",')

        # Add buildCommand only if RUNCOMMANDS.build is non-empty
        if RUNCOMMANDS.build:
            lines.append(f'  "buildCommand": "uv run {PKG_NAME} runbuild",')

        lines.extend(
            [
                '  "rewrites": [',
                "    {",
                '      "source": "/(.*)",',
                '      "destination": "/api/server"',
                "    }",
                "  ]",
                "}",
            ]
        )

        return "\n".join(lines) + "\n"


class Command(BaseCommand):
    help: str = "Generate configuration files (e.g., .env.example, vercel.json, asgi.py, wsgi.py, .pg_service.conf, pgpass.conf / .pgpass, ssh config)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "-f",
            "--file",
            dest="file",
            choices=[opt.value for opt in FileOption],
            type=FileOption,
            required=True,
            help=f"Specify which file to generate (options: {', '.join(o.value for o in FileOption)}).",
        )
        parser.add_argument(
            "-y",
            "--force",
            dest="force",
            action="store_true",
            help="Force overwrite without confirmation.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        file_option: FileOption = FileOption(options["file"])
        force: bool = options["force"]

        generators: dict[FileOption, Type[FileGenerator]] = {
            FileOption.VERCEL: VercelFileGenerator,
            FileOption.SERVER: ServerFileGenerator,
            FileOption.PG_SERVICE: PgServiceFileGenerator,
            FileOption.PGPASS: PgPassFileGenerator,
            FileOption.SSH_CONFIG: SSHConfigFileGenerator,
            FileOption.ENV: EnvFileGenerator,
        }

        generator_class: Type[FileGenerator] = generators[file_option]
        generator = generator_class()
        generator.create(force=force)
