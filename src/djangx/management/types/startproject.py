"""Startproject type definitions."""

from dataclasses import dataclass
from pathlib import Path
from typing import NotRequired, TypedDict

from ..enums import DatabaseEnum, PresetEnum

__all__: list[str] = [
    "PresetDataclass",
    "DatabaseOptionsDict",
    "DatabaseDict",
    "DatabasesDict",
    "DatabaseDataclass",
    "PGConfigMethodDataclass",
]


@dataclass(frozen=True)
class PresetDataclass:
    """Project preset configuration."""

    preset: PresetEnum
    name: str
    description: str
    required_database: DatabaseEnum | None
    required_pg_config: bool | None
    dependencies: tuple[str, ...]
    generated_files: tuple[str, ...]
    learn_more_url: str | None


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


@dataclass(frozen=True)
class DatabaseDataclass:
    """Database backend configuration."""

    backend: DatabaseEnum
    name: str
    description: str
    dependencies: tuple[str, ...]
    requires_pg_config: bool
    learn_more_url: str | None


@dataclass(frozen=True)
class PGConfigMethodDataclass:
    """PostgreSQL configuration method."""

    value: bool
    name: str
    description: str
    cli_flag: str
    files_required: tuple[str, ...]
    learn_more_url: str | None
