from ... import Conf, ConfField


class OrgConf(Conf):
    """Organization-related configuration settings."""

    name = ConfField(
        env="ORG_NAME",
        toml="org.name",
        type=str,
    )
    short_name = ConfField(
        env="ORG_SHORT_NAME",
        toml="org.short-name",
        type=str,
    )
    description = ConfField(
        env="ORG_DESCRIPTION",
        toml="org.description",
        type=str,
    )
    logo_url = ConfField(
        env="ORG_LOGO_URL",
        toml="org.logo-url",
        default="ui/img/logo.png",
        type=str,
    )
    favicon_url = ConfField(
        env="ORG_FAVICON_URL",
        toml="org.favicon-url",
        default="ui/img/favicon.ico",
        type=str,
    )
    apple_touch_icon_url = ConfField(
        env="ORG_APPLE_TOUCH_ICON_URL",
        toml="org.apple-touch-icon-url",
        default="ui/img/apple-touch-icon.png",
        type=str,
    )


ORG = OrgConf()


__all__: list[str] = ["ORG"]
