from enum import StrEnum
from typing import Any

from christianwhocodes.generators import (
    FileGenerator,
    FileGeneratorOption,
    PgPassFileGenerator,
    PgServiceFileGenerator,
    SSHConfigFileGenerator,
)
from django.core.management.base import BaseCommand, CommandParser

from .generators import EnvFileGenerator, ServerFileGenerator, VercelFileGenerator


class FileOption(StrEnum):
    PG_SERVICE = FileGeneratorOption.PG_SERVICE.value
    PGPASS = FileGeneratorOption.PGPASS.value
    SSH_CONFIG = FileGeneratorOption.SSH_CONFIG.value
    ENV = "env"
    SERVER = "server"
    VERCEL = "vercel"


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

        generators: dict[FileOption, type[FileGenerator]] = {
            FileOption.VERCEL: VercelFileGenerator,
            FileOption.SERVER: ServerFileGenerator,
            FileOption.PG_SERVICE: PgServiceFileGenerator,
            FileOption.PGPASS: PgPassFileGenerator,
            FileOption.SSH_CONFIG: SSHConfigFileGenerator,
            FileOption.ENV: EnvFileGenerator,
        }

        generator_class: type[FileGenerator] = generators[file_option]
        generator = generator_class()
        generator.create(force=force)
