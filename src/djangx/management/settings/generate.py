from pathlib import Path

from ... import PROJECT_API_DIR, PROJECT_DIR, Conf, ConfField


class FileGeneratorPathsConf(Conf):
    """Generated files configuration settings."""

    dotenv_example = ConfField(
        type=Path,
        default=PROJECT_DIR / ".env.example",
    )
    vercel_json = ConfField(
        type=Path,
        default=PROJECT_DIR / "vercel.json",
    )
    server_py = ConfField(
        type=Path,
        default=PROJECT_API_DIR / "server.py",
    )


FILE_GENERATOR_PATHS = FileGeneratorPathsConf()


__all__: list[str] = ["FILE_GENERATOR_PATHS"]
