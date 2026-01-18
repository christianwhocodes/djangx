from ... import Conf, ConfField


class RunCommandsConf(Conf):
    """Install/Build Commands to be executed settings."""

    install = ConfField(
        env="RUNCOMMANDS_INSTALL",
        toml="runcommands.install",
        type=list,
    )
    build = ConfField(
        env="RUNCOMMANDS_BUILD",
        toml="runcommands.build",
        default=["makemigrations", "migrate", "collectstatic --noinput"],
        type=list,
    )


RUNCOMMANDS = RunCommandsConf()


__all__: list[str] = ["RUNCOMMANDS"]
