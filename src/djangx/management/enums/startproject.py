from enum import StrEnum

__all__: list[str] = [
    "PresetEnum",
    "DatabaseEnum",
]


class PresetEnum(StrEnum):
    DEFAULT = "default"
    VERCEL = "vercel"


class DatabaseEnum(StrEnum):
    """Available database backends.

    These values are used in:
    - CLI flags (--database)
    - Interactive prompts
    - pyproject.toml configuration
    - DATABASE_CONFIGS mapping (mappings.py)
    """

    SQLITE3 = "sqlite3"
    POSTGRESQL = "postgresql"
