"""Root app configuration."""

from django.apps import AppConfig

from . import PACKAGE


class DjangXConfig(AppConfig):
    """Root app configuration."""

    name = PACKAGE.name
