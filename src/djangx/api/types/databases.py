from pathlib import Path
from typing import NotRequired, TypedDict


class DatabaseOptionsDict(TypedDict, total=False):
    """Type definition for database OPTIONS dictionary."""

    service: str
    pool: bool
    sslmode: str


class DatabaseDict(TypedDict):
    """Type definition for default database configuration."""

    ENGINE: str
    NAME: str | Path
    USER: NotRequired[str | None]
    PASSWORD: NotRequired[str | None]
    HOST: NotRequired[str | None]
    PORT: NotRequired[str | None]
    OPTIONS: NotRequired[DatabaseOptionsDict]


class DatabasesDict(TypedDict):
    """Type definition for DATABASES setting."""

    default: DatabaseDict


__all__: list[str] = ["DatabaseOptionsDict", "DatabaseDict", "DatabasesDict"]
