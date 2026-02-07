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
    """Project preset configuration definition.

    Attributes:
        preset: The preset type enum value
        name: Human-readable display name
        description: Brief description of this preset
        required_database: Required database backend (None = any)
        required_pg_config: Required PG config method (None = any)
        dependencies: Additional Python packages for this preset
        generated_files: Files that will be generated for this preset
        learn_more_url: Documentation URL for this preset
    """

    preset: PresetEnum
    name: str
    description: str
    required_database: DatabaseEnum | None
    required_pg_config: bool | None
    dependencies: tuple[str, ...]
    generated_files: tuple[str, ...]
    learn_more_url: str | None


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


@dataclass(frozen=True)
class DatabaseDataclass:
    """Database backend configuration definition.

    Attributes:
        backend: The database backend enum value
        name: Human-readable display name
        description: Brief description of when to use this database
        dependencies: Python packages required for this database
        requires_pg_config: Whether PostgreSQL config method is needed
        learn_more_url: Documentation URL for this database
    """

    backend: DatabaseEnum
    name: str
    description: str
    dependencies: tuple[str, ...]
    requires_pg_config: bool
    learn_more_url: str | None


@dataclass(frozen=True)
class PGConfigMethodDataclass:
    """PostgreSQL configuration method definition.

    Attributes:
        value: The boolean value (True = env vars, False = service files)
        name: Human-readable name
        description: Detailed description
        cli_flag: CLI flag name for this method
        files_required: List of config files needed (empty for env vars)
        learn_more_url: Documentation URL
    """

    value: bool
    name: str
    description: str
    cli_flag: str
    files_required: tuple[str, ...]
    learn_more_url: str | None
