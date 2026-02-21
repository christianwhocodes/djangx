"""Startproject enums."""

from enum import StrEnum

__all__: list[str] = [
    "PresetEnum",
    "DatabaseEnum",
]


class PresetEnum(StrEnum):
    """Available project presets."""

    DEFAULT = "default"
    VERCEL = "vercel"


class DatabaseEnum(StrEnum):
    """Available database backends."""

    SQLITE3 = "sqlite3"
    POSTGRESQL = "postgresql"
