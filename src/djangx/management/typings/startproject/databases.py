"""Databases definitions."""

from pathlib import Path
from typing import NotRequired, TypedDict


class DatabaseOptionsDict(TypedDict, total=False):
    """Database OPTIONS dict."""

    service: str
    pool: bool
    sslmode: str


class DatabaseDict(TypedDict):
    """Single database configuration entry."""

    ENGINE: str
    NAME: str | Path
    USER: NotRequired[str | None]
    PASSWORD: NotRequired[str | None]
    HOST: NotRequired[str | None]
    PORT: NotRequired[str | None]
    OPTIONS: NotRequired[DatabaseOptionsDict]


class DatabasesDict(TypedDict):
    """DATABASES setting dict."""

    default: DatabaseDict


__all__: list[str] = [
    "DatabaseOptionsDict",
    "DatabaseDict",
    "DatabasesDict",
]
