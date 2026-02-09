"""Run commands settings configuration."""

from .config import ConfField, SettingConfig

__all__: list[str] = ["RUNCOMMANDS"]


class _RunCommandsConf(SettingConfig):
    """Configuration for install and build management commands.

    Defines the lists of management commands to execute during
    the install and build phases of the project lifecycle.
    """

    install = ConfField(
        type=list,
        env="RUNCOMMANDS_INSTALL",
        toml="runcommands.install",
        default=[],
    )
    build = ConfField(
        type=list,
        env="RUNCOMMANDS_BUILD",
        toml="runcommands.build",
        default=["makemigrations", "migrate", "collectstatic --noinput"],
    )


RUNCOMMANDS = _RunCommandsConf()
