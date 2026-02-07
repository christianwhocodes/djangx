from enum import StrEnum

from christianwhocodes import FileGeneratorOption as BaseFileGeneratorOption

__all__: list[str] = ["FileGeneratorOptionEnum"]


class FileGeneratorOptionEnum(StrEnum):
    """File generation options.

    These values are used with the framework's file generation system
    to create various configuration and deployment files.

    Inherited from christianwhocodes.generators:
    - PG_SERVICE: PostgreSQL service configuration
    - PGPASS: PostgreSQL password file
    - SSH_CONFIG: SSH configuration

    Framework-specific:
    - ENV: Environment variables file
    - SERVER: Server deployment file
    - VERCEL: Vercel configuration
    """

    PG_SERVICE = BaseFileGeneratorOption.PG_SERVICE.value
    PGPASS = BaseFileGeneratorOption.PGPASS.value
    SSH_CONFIG = BaseFileGeneratorOption.SSH_CONFIG.value
    ENV = "env"
    SERVER = "server"
    VERCEL = "vercel"
