"""Generate Env spec for .env.example with all available env vars."""

from ..conf import BaseConf

__all__: list[str] = ["GENERATED_ENV_FIELDS"]

GENERATED_ENV_FIELDS = BaseConf.get_env_fields()
