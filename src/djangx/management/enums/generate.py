"""File generation enums."""

from enum import StrEnum

from christianwhocodes import FileGeneratorOption as BaseFileGeneratorOption

__all__: list[str] = ["FileGeneratorOptionEnum"]


class FileGeneratorOptionEnum(StrEnum):
    """Available file generation options."""

    PG_SERVICE = BaseFileGeneratorOption.PG_SERVICE.value
    PGPASS = BaseFileGeneratorOption.PGPASS.value
    SSH_CONFIG = BaseFileGeneratorOption.SSH_CONFIG.value
    ENV = "env"
    SERVER = "server"
    VERCEL = "vercel"
