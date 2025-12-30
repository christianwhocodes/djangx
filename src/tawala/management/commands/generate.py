from enum import StrEnum
from pathlib import Path
from typing import Any, Type

from christianwhocodes.generators.file import (
    FileGenerator,
    FileGeneratorOption,
    PgPassFileGenerator,
    PgServiceFileGenerator,
    SSHConfigFileGenerator,
)
from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser


class FileOption(StrEnum):
    PG_SERVICE = FileGeneratorOption.PG_SERVICE.value
    PGPASS = FileGeneratorOption.PGPASS.value
    SSH_CONFIG = FileGeneratorOption.SSH_CONFIG.value
    VERCEL = "vercel"
    ASGI = "asgi"
    WSGI = "wsgi"


class VercelJSONFileGenerator(FileGenerator):
    """
    Generator for Vercel configuration file (vercel.json).

    Creates a vercel.json file in the Tawala project base directory.
    Useful for deploying Tawala apps to Vercel with custom install/build commands.
    """

    @property
    def file_path(self) -> Path:
        """Return the path for the vercel.json."""
        return settings.BASE_DIR / "vercel.json"

    @property
    def data(self) -> str:
        """Return template content for vercel.json."""
        return (
            "{\n"
            '  "$schema": "https://openapi.vercel.sh/vercel.json",\n'
            f'  "installCommand": "uv run {settings.PKG_NAME} runinstall",\n'
            f'  "buildCommand": "uv run {settings.PKG_NAME} runbuild",\n'
            '  "rewrites": [\n'
            "    {\n"
            '      "source": "/(.*)",\n'
            '      "destination": "/api/asgi"\n'
            "    }\n"
            "  ]\n"
            "}\n"
        )


class ASGIFileGenerator(FileGenerator):
    """
    Generator for ASGI configuration file (asgi.py).

    Creates an asgi.py file in the API directory.
    Required for running Tawala apps with ASGI servers.
    """

    @property
    def file_path(self) -> Path:
        """Return the path for the asgi.py"""
        return settings.API_DIR / "asgi.py"

    @property
    def data(self) -> str:
        """Return template content for asgi.py."""
        return f"from {settings.PKG_NAME} import asgi\n\napp = asgi.application\n"


class WSGIFileGenerator(FileGenerator):
    """
    Generator for WSGI configuration file (wsgi.py).

    Creates a wsgi.py file in the API directory.
    Required for running Tawala apps with WSGI servers.
    """

    @property
    def file_path(self) -> Path:
        """Return the path for the wsgi.py."""
        return settings.API_DIR / "wsgi.py"

    @property
    def data(self) -> str:
        """Return template content for wsgi.py file."""
        return f"from {settings.PKG_NAME} import wsgi\n\napp = wsgi.application\n"


class Command(BaseCommand):
    help: str = "Generate configuration files (e.g., vercel.json, asgi.py, wsgi.py, .pg_service.conf, pgpass.conf / .pgpass, ssh config)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "-f",
            "--file",
            choices=[opt.value for opt in FileOption],
            type=FileOption,
            required=True,
            help=f"Specify which file to generate (options: {', '.join(o.value for o in FileOption)}).",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force overwrite without confirmation.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        file_option: FileOption = FileOption(options["file"])
        force: bool = options["force"]

        generators: dict[FileOption, Type[FileGenerator]] = {
            FileOption.VERCEL: VercelJSONFileGenerator,
            FileOption.ASGI: ASGIFileGenerator,
            FileOption.WSGI: WSGIFileGenerator,
            FileOption.PG_SERVICE: PgServiceFileGenerator,
            FileOption.PGPASS: PgPassFileGenerator,
            FileOption.SSH_CONFIG: SSHConfigFileGenerator,
        }

        generator_class: Type[FileGenerator] = generators[file_option]
        generator: FileGenerator = generator_class()
        generator.create(force=force)
