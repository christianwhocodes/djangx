from typing import TypedDict


class StorageBackendDict(TypedDict, total=False):
    """Type definition for individual storage backend configuration."""

    BACKEND: str


class StoragesDict(TypedDict):
    """Type definition for STORAGES setting."""

    staticfiles: StorageBackendDict
    default: StorageBackendDict


__all__: list[str] = ["StorageBackendDict", "StoragesDict"]
