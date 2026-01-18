from typing import get_args

from ... import Conf, ConfField
from ..types import SocialKey


class SocialUrlsConf(Conf):
    """Social Media configuration settings."""

    facebook = ConfField(env="SOCIAL_URLS_FACEBOOK", toml="social-urls.facebook", type=str)
    twitter_x = ConfField(env="SOCIAL_URLS_TWITTER_X", toml="social-urls.twitter-x", type=str)
    instagram = ConfField(env="SOCIAL_URLS_INSTAGRAM", toml="social-urls.instagram", type=str)
    linkedin = ConfField(env="SOCIAL_URLS_LINKEDIN", toml="social-urls.linkedin", type=str)
    whatsapp = ConfField(env="SOCIAL_URLS_WHATSAPP", toml="social-urls.whatsapp", type=str)
    youtube = ConfField(env="SOCIAL_URLS_YOUTUBE", toml="social-urls.youtube", type=str)


SOCIAL_URLS = SocialUrlsConf()
SOCIAL_PLATFORMS: tuple[str, ...] = get_args(SocialKey)
SOCIAL_PLATFORM_ICONS_MAP: dict[str, str] = {
    SOCIAL_PLATFORMS[0]: "bi bi-facebook",
    SOCIAL_PLATFORMS[1]: "bi bi-twitter-x",
    SOCIAL_PLATFORMS[2]: "bi bi-instagram",
    SOCIAL_PLATFORMS[3]: "bi bi-linkedin",
    SOCIAL_PLATFORMS[4]: "bi bi-whatsapp",
    SOCIAL_PLATFORMS[5]: "bi bi-youtube",
}


__all__: list[str] = ["SOCIAL_URLS", "SOCIAL_PLATFORMS", "SOCIAL_PLATFORM_ICONS_MAP"]
