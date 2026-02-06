from enum import StrEnum


class DatabaseBackend(StrEnum):
    """Available database backends.

    These values are used in:
    - CLI flags (--database)
    - Interactive prompts
    - pyproject.toml configuration
    - DATABASE_CONFIGS mapping (maps.py)
    """

    SQLITE3 = "sqlite3"
    POSTGRESQL = "postgresql"
