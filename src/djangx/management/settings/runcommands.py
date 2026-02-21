"""Run commands settings."""

from .config import ConfField, SettingConf

__all__: list[str] = ["RUNCOMMANDS"]


class _RunCommandsConf(SettingConf):
    """Install and build command lists."""

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
