"""Static files and storage settings."""

from pathlib import Path
from typing import TypedDict

from ....constants import Package, StorageChoices
from ...conf import BaseConf, ConfField

__all__: list[str] = [
    "STORAGES",
    "BLOB_READ_WRITE_TOKEN",
    "STATIC_ROOT",
    "STATIC_URL",
    "MEDIA_ROOT",
    "MEDIA_URL",
]


class _StorageConf(BaseConf):
    """Storage backend settings."""

    backend = ConfField(
        type=str,
        choices=[StorageChoices.FILESYSTEM, StorageChoices.VERCELBLOB],
        env="STORAGE_BACKEND",
        toml="storage.backend",
        default=StorageChoices.FILESYSTEM,
    )
    # NOTE: This token is only relevant for the Vercel Blob Storage backend, but we include it here for simplicity. It will be ignored if the filesystem backend is used.
    token = ConfField(
        type=str,
        env="BLOB_READ_WRITE_TOKEN",
        toml="storage.blob-token",
        default="",
    )


_STORAGE = _StorageConf()


class _StorageBackendDict(TypedDict, total=False):
    """Individual storage backend entry."""

    BACKEND: str


class _StoragesDict(TypedDict):
    """STORAGES setting dict."""

    staticfiles: _StorageBackendDict
    default: _StorageBackendDict


def _get_storages_config() -> _StoragesDict:
    """Build the STORAGES setting based on configured backend."""
    backend: str = _STORAGE.backend
    storage_backend: str

    match backend:
        case StorageChoices.FILESYSTEM:
            storage_backend = "django.core.files.storage.FileSystemStorage"
        case StorageChoices.VERCELBLOB:
            storage_backend = f"{Package.NAME}.management.backends.VercelBlobStorageBackend"
        case _:
            raise ValueError(f"Unsupported storage backend: {backend}")

    return {
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
        "default": {
            "BACKEND": storage_backend,
        },
    }


STORAGES: _StoragesDict = _get_storages_config()

BLOB_READ_WRITE_TOKEN: str = _STORAGE.token

STATIC_ROOT: Path = Path.cwd() / "public" / "static"

STATIC_URL: str = "static/"

MEDIA_ROOT: Path = Path.cwd() / "public" / "media"

MEDIA_URL: str = "media/"
