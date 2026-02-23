"""Startproject enums."""

from enum import StrEnum

__all__: list[str] = ["DatabaseEnum", "StorageEnum", "PresetEnum", "PostgresFlagEnum"]


class DatabaseEnum(StrEnum):
    """Available database backends."""

    SQLITE3 = "sqlite3"
    POSTGRESQL = "postgresql"


class StorageEnum(StrEnum):
    """Available storage backends."""

    FILESYSTEM = "filesystem"
    VERCELBLOB = "vercelblob"


class PresetEnum(StrEnum):
    """Available project presets."""

    DEFAULT = "default"
    VERCEL = "vercel"


class PostgresFlagEnum(StrEnum):
    """Flag to indicate whether to use environment variables for PostgreSQL configuration."""

    USE_ENV_VARS = "--pg-use-env-vars"
