from ... import PKG_UI_NAME, Conf, ConfField


class OrgConf(Conf):
    """Organization-related configuration settings."""

    name = ConfField(
        type=str,
        env="ORG_NAME",
        toml="org.name",
        default="",
    )
    short_name = ConfField(
        type=str,
        env="ORG_SHORT_NAME",
        toml="org.short-name",
        default="",
    )
    description = ConfField(
        type=str,
        env="ORG_DESCRIPTION",
        toml="org.description",
        default="",
    )
    logo_url = ConfField(
        type=str,
        env="ORG_LOGO_URL",
        toml="org.logo-url",
        default=f"{PKG_UI_NAME}/img/logo.png",
    )
    favicon_url = ConfField(
        type=str,
        env="ORG_FAVICON_URL",
        toml="org.favicon-url",
        default=f"{PKG_UI_NAME}/img/favicon.ico",
    )
    apple_touch_icon_url = ConfField(
        type=str,
        env="ORG_APPLE_TOUCH_ICON_URL",
        toml="org.apple-touch-icon-url",
        default=f"{PKG_UI_NAME}/img/apple-touch-icon.png",
    )


ORG = OrgConf()


__all__: list[str] = ["ORG"]
