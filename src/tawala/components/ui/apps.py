from django.apps import AppConfig

from ...conf.pre import PKG


class UIConfig(AppConfig):
    name = f"{PKG.name}.components.ui"
