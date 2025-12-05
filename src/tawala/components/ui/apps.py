from django.apps import AppConfig

from ... import PKG


class UIConfig(AppConfig):
    name = f"{PKG.name}.components.ui"
