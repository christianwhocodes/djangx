from typing import TypedDict

from .conf import Conf, ConfField


class OrgConf(Conf):
    """Organization-related configuration settings."""

    name = ConfField(env="ORG_NAME", toml="org.name", type=str)
    short_name = ConfField(env="ORG_SHORT_NAME", toml="org.short-name", type=str)
    description = ConfField(env="ORG_DESCRIPTION", toml="org.description", type=str)


class OrgDict(TypedDict):
    name: str
    short_name: str
    description: str


_org = OrgConf()

ORG: OrgDict = {
    "name": _org.name or "Tawala",
    "short_name": _org.short_name or "Tawala",
    "description": _org.description or "Tawala Application",
}

__all__ = ["ORG"]
