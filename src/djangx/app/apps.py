from django.apps import AppConfig as BaseAppConfig

from .. import PACKAGE


class AppConfig(BaseAppConfig):
    name = f"{PACKAGE.name}.app"
