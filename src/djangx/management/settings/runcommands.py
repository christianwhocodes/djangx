from ... import Conf, ConfField


class RunCommandsConf(Conf):
    """Install/Build Commands to be executed settings."""

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


RUNCOMMANDS = RunCommandsConf()


__all__: list[str] = ["RUNCOMMANDS"]
