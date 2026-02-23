"""Static files and storage settings."""

from pathlib import Path

from .... import PACKAGE, PROJECT
from ...definitions import StoragesDict
from ..base import BaseConf, ConfField


class _StorageConf(BaseConf):
    """Storage backend settings."""

    backend = ConfField(
        type=str,
        choices=["filesystem", "vercelblob"],
        env="STORAGE_BACKEND",
        toml="storage.backend",
        default="filesystem",
    )
    # vercelblob specific
    token = ConfField(
        type=str,
        env="BLOB_READ_WRITE_TOKEN",
        toml="storage.blob-token",
        default="",
    )


_STORAGE = _StorageConf()


def _get_storages_config() -> StoragesDict:
    """Build the STORAGES setting based on configured backend."""
    backend: str = _STORAGE.backend
    storage_backend: str

    match backend:
        case "filesystem" | "local" | "fs":
            storage_backend = "django.core.files.storage.FileSystemStorage"
        case "blob" | "vercel" | "vercel-blob":
            storage_backend = f"{PACKAGE.name}.management.backends.VercelBlobStorageBackend"
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


STORAGES: StoragesDict = _get_storages_config()

BLOB_READ_WRITE_TOKEN: str = _STORAGE.token

STATIC_ROOT: Path = PROJECT.public_dir / "static"

STATIC_URL: str = "static/"

MEDIA_ROOT: Path = PROJECT.public_dir / "media"

MEDIA_URL: str = "media/"


__all__: list[str] = [
    "STORAGES",
    "BLOB_READ_WRITE_TOKEN",
    "STATIC_ROOT",
    "STATIC_URL",
    "MEDIA_ROOT",
    "MEDIA_URL",
]
