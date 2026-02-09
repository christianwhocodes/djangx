"""App configuration."""

from django.apps import AppConfig as BaseAppConfig

from .. import PACKAGE


class AppConfig(BaseAppConfig):
    """App configuration."""

    name = f"{PACKAGE.name}.app"
