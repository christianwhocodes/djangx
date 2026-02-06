from enum import StrEnum


class DatabaseBackend(StrEnum):
    """Available database backends."""

    SQLITE3 = "sqlite3"
    POSTGRESQL = "postgresql"
