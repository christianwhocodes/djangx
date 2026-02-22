"""Management command for generating configuration files."""

import builtins
import pathlib
from collections.abc import Callable
from typing import Any, cast

from christianwhocodes import (
    FileGenerator,
    FileSpec,
    get_pg_service_spec,
    get_pgpass_spec,
)
from django.core.management.base import BaseCommand, CommandParser

from ... import PACKAGE, PROJECT
from ..enums import FileGeneratorOptions


def _get_api_server_spec() -> FileSpec:
    """Return the FileSpec for api/server.py."""
    content = (
        f"from {PACKAGE.name}.management.backends import SERVER_APPLICATION as application\n\n"
        "app = application\n"
    )
    return FileSpec(path=PROJECT.api_dir / "server.py", content=content)


def _get_vercel_spec() -> FileSpec:
    """Return the FileSpec for vercel.json."""
    lines = [
        "{",
        '  "$schema": "https://openapi.vercel.sh/vercel.json",',
        f'  "installCommand": "uv run {PACKAGE.name} runinstall",',
        f'  "buildCommand": "uv run {PACKAGE.name} runbuild",',
        '  "rewrites": [',
        "    {",
        '      "source": "/(.*)",',
        '      "destination": "/api/server"',
        "    }",
        "  ]",
        "}",
    ]
    return FileSpec(path=PROJECT.base_dir / "vercel.json", content="\n".join(lines) + "\n")


def _get_env_spec() -> FileSpec:
    """Return the FileSpec for .env.example with all available env vars."""
    from ..conf import ManagementConf

    lines: list[str] = []

    # Add header
    lines.extend(_env_header())

    # Get all fields from Conf subclasses
    env_fields = ManagementConf.get_env_fields()

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
        lines.extend(_env_section_header(class_name))

        # Process each field in this class
        for field in fields:
            env_var = field["env"]
            toml_key = field["toml"]
            choices_key = field["choices"]
            default_value = field["default"]
            field_type = field["type"]

            # Add field documentation with proper format hints
            lines.append(
                f"# Variable: {_env_format_variable_hint(env_var, choices_key, field_type)}"
            )
            if toml_key:
                lines.append(f"# TOML Key: {toml_key}")

            # Format default value for display
            if default_value is not None:
                formatted_default = _env_format_default_value(default_value, field_type)
                lines.append(f"# Default: {formatted_default}")
            else:
                lines.append("# Default: (none)")

            lines.append(f"# {env_var}=")

            lines.append("")

        lines.append("")

    # Add footer
    lines.extend(_env_footer())

    return FileSpec(path=PROJECT.base_dir / ".env.example", content="\n".join(lines))


# ---------------------------------------------------------------------------
# .env.example helpers
# ---------------------------------------------------------------------------


def _env_header() -> list[str]:
    """File header lines."""
    return [
        "# " + "=" * 78,
        f"# {PACKAGE.display_name} Environment Configuration",
        "# " + "=" * 78,
        "#",
        "# This file contains all available environment variables for configuration.",
        "#",
        "# Configuration Priority: ENV > TOML > Default",
        "# " + "=" * 78,
        "",
    ]


def _env_section_header(class_name: str) -> list[str]:
    """Section header for a config class."""
    return [
        "# " + "-" * 78,
        f"# {class_name} Configuration",
        "# " + "-" * 78,
        "",
    ]


def _env_footer() -> list[str]:
    """File footer lines."""
    return [
        "# " + "=" * 78,
        "# End of Configuration",
        "# " + "=" * 78,
    ]


def _env_format_choices(choices: list[str]) -> str:
    """Format choices as quoted alternatives."""
    return " | ".join(f'"{choice}"' for choice in choices)


def _env_get_type_example(field_type: type) -> str:
    """Return example value string for a field type."""
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


def _env_format_variable_hint(env_var: str, choices_key: list[str] | None, field_type: type) -> str:
    """Format a variable hint showing expected syntax."""
    if choices_key:
        return f"{env_var}={_env_format_choices(choices_key)}"
    return f"{env_var}={_env_get_type_example(field_type)}"


def _env_format_default_value(value: Any, field_type: type) -> str:
    """Format a default value for display in comments."""
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


# ---------------------------------------------------------------------------
# Command implementation
# ---------------------------------------------------------------------------


class Command(BaseCommand):
    """Generate configuration files."""

    help: str = "Generate configuration files (e.g., .env.example, vercel.json, asgi.py, wsgi.py, .pg_service.conf, pgpass.conf / .pgpass)."

    def add_arguments(self, parser: CommandParser) -> None:
        """Add command arguments."""
        parser.add_argument(
            "file",
            choices=[opt.value for opt in FileGeneratorOptions],
            type=FileGeneratorOptions,
            help=f"Which file to generate (options: {', '.join(o.value for o in FileGeneratorOptions)}).",
        )
        parser.add_argument(
            "-f",
            "--force",
            dest="force",
            action="store_true",
            help="Force overwrite without confirmation.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute the generate command."""
        file_option: FileGeneratorOptions = FileGeneratorOptions(options["file"])
        force: bool = options["force"]

        generators: dict[FileGeneratorOptions, Callable[[], FileSpec]] = {
            FileGeneratorOptions.VERCEL_JSON: _get_vercel_spec,
            FileGeneratorOptions.API_SERVER_PY: _get_api_server_spec,
            FileGeneratorOptions.PG_SERVICE: get_pg_service_spec,
            FileGeneratorOptions.PGPASS: get_pgpass_spec,
            FileGeneratorOptions.DOTENV_EXAMPLE: _get_env_spec,
        }

        spec: FileSpec = generators[file_option]()
        generator = FileGenerator(spec)
        generator.create(overwrite=force)
