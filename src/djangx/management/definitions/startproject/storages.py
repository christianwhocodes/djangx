"""Storage type definitions."""

from typing import TypedDict


class _StorageBackendDict(TypedDict, total=False):
    """Individual storage backend entry."""

    BACKEND: str


class StoragesDict(TypedDict):
    """STORAGES setting dict."""

    staticfiles: _StorageBackendDict
    default: _StorageBackendDict


__all__: list[str] = ["StoragesDict"]
