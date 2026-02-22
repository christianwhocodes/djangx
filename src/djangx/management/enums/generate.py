"""File generation enums."""

from enum import StrEnum

__all__: list[str] = ["FileGeneratorOptions"]


class FileGeneratorOptions(StrEnum):
    """Available file generation options."""

    DOTENV_EXAMPLE = ".env.example"
    API_SERVER_PY = "api/server.py"
    VERCEL_JSON = "vercel.json"
    PG_SERVICE = "pg_service"
    PGPASS = "pgpass"
