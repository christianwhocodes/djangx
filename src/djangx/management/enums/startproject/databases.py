"""Databases enums."""

from enum import StrEnum

__all__: list[str] = [
    "DatabaseEnum",
]


class DatabaseEnum(StrEnum):
    """Available database backends."""

    SQLITE3 = "sqlite3"
    POSTGRESQL = "postgresql"
