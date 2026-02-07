# ==============================================================================
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/stable/howto/static-files/

# Storage & Media files (User-uploaded content)
# https://docs.djangoproject.com/en/stable/ref/settings/#storages
# https://docs.djangoproject.com/en/stable/ref/settings/#media-files
# ==============================================================================
from pathlib import Path

from ... import PACKAGE, PROJECT
from ..types import StoragesDict
from .config import ConfField, SettingConfig

__all__: list[str] = [
    "STORAGES",
    "BLOB_READ_WRITE_TOKEN",
    "STATIC_ROOT",
    "STATIC_URL",
    "MEDIA_ROOT",
    "MEDIA_URL",
]


class _StorageConf(SettingConfig):
    """Storage configuration settings."""

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
    """Generate storage configuration based on backend type."""

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
