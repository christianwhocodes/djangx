"""Generate Env spec for .env.example with all available env vars."""

from ._conf import ManagementConf

__all__: list[str] = ["GENERATED_ENV_FIELDS"]

GENERATED_ENV_FIELDS = ManagementConf.get_env_fields()
