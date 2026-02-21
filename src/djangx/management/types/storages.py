"""Storage type definitions."""

from typing import TypedDict

__all__: list[str] = ["StorageBackendDict", "StoragesDict"]


class StorageBackendDict(TypedDict, total=False):
    """Individual storage backend entry."""

    BACKEND: str


class StoragesDict(TypedDict):
    """STORAGES setting dict."""

    staticfiles: StorageBackendDict
    default: StorageBackendDict
