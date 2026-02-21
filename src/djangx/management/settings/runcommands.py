"""Run commands settings."""

from .. import ConfField, ManagementConf

__all__: list[str] = ["RUNCOMMANDS"]


class _RunCommandsConf(ManagementConf):
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
