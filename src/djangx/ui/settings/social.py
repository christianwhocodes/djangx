from typing import get_args

from ... import Conf, ConfField
from ..types import SocialKey


class SocialUrlsConf(Conf):
    """Social Media configuration settings."""

    facebook = ConfField(
        type=str,
        env="SOCIAL_URLS_FACEBOOK",
        toml="social-urls.facebook",
        default="",
    )
    twitter_x = ConfField(
        type=str,
        env="SOCIAL_URLS_TWITTER_X",
        toml="social-urls.twitter-x",
        default="",
    )
    instagram = ConfField(
        type=str,
        env="SOCIAL_URLS_INSTAGRAM",
        toml="social-urls.instagram",
        default="",
    )
    linkedin = ConfField(
        type=str,
        env="SOCIAL_URLS_LINKEDIN",
        toml="social-urls.linkedin",
        default="",
    )
    whatsapp = ConfField(
        type=str,
        env="SOCIAL_URLS_WHATSAPP",
        toml="social-urls.whatsapp",
        default="",
    )
    youtube = ConfField(
        type=str,
        env="SOCIAL_URLS_YOUTUBE",
        toml="social-urls.youtube",
        default="",
    )


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
