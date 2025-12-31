from typing import TypedDict

from .conf import Conf, ConfField


class URLsConf(Conf):
    """URL-related configuration settings."""

    home = ConfField(env="URLS_HOME", toml="urls.home", type=str)
    api = ConfField(env="URLS_API", toml="urls.api", type=str)


_urls = URLsConf()


class URLsDict(TypedDict):
    home: str
    api: str


URLS: URLsDict = {
    "home": _urls.home or "/",
    "api": _urls.api or "/api",
}

__all__ = ["URLS"]
