"""Type definitions for storage backends."""

from typing import TypedDict

__all__: list[str] = ["StorageBackendDict", "StoragesDict"]


class StorageBackendDict(TypedDict, total=False):
    """Type definition for individual storage backend configuration."""

    BACKEND: str


class StoragesDict(TypedDict):
    """Type definition for STORAGES setting."""

    staticfiles: StorageBackendDict
    default: StorageBackendDict
