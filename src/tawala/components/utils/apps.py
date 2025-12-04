from django.apps import AppConfig

from ...conf.pre import PKG


class UtilsConfig(AppConfig):
    name = f"{PKG.name}.components.utils"

    def ready(self):
        # Remove runserver command
        from django.core.management import get_commands

        commands = get_commands()
        if "runserver" in commands:
            commands.pop("runserver")
