"""Installed apps, middleware, and template settings."""

from .... import PACKAGE, PROJECT
from ...enums import AppEnum
from ..base import BaseConf, ConfField


class _AppsConf(BaseConf):
    """Installed applications settings."""

    extend = ConfField(
        type=list,
        env="APPS_EXTEND",
        toml="apps.extend",
        default=[],
    )
    remove = ConfField(
        type=list,
        env="APPS_REMOVE",
        toml="apps.remove",
        default=[],
    )


_APPS_CONF = _AppsConf()


def _get_installed_apps() -> list[str]:
    """Build the final INSTALLED_APPS list. Order: local -> third-party -> contrib."""
    base_apps: list[str] = [
        PROJECT.home_app_name,
        PACKAGE.name,
        f"{PACKAGE.name}.{PACKAGE.main_app_name}",
    ]

    third_party_apps: list[str] = [
        AppEnum.HTTP_COMPRESSION,
        AppEnum.MINIFY_HTML,
        AppEnum.BROWSER_RELOAD,
        AppEnum.WATCHFILES,
    ]

    contrib_apps: list[str] = [
        AppEnum.ADMIN,
        AppEnum.AUTH,
        AppEnum.CONTENTTYPES,
        AppEnum.SESSIONS,
        AppEnum.MESSAGES,
        AppEnum.STATICFILES,
    ]

    # Collect apps that should be removed except for base apps
    apps_to_remove: list[str] = [app for app in _APPS_CONF.remove if app not in base_apps]

    # Remove apps that are in the remove list
    contrib_apps: list[str] = [app for app in contrib_apps if app not in apps_to_remove]
    third_party_apps: list[str] = [app for app in third_party_apps if app not in apps_to_remove]

    # Combine
    all_apps: list[str] = _APPS_CONF.extend + base_apps + third_party_apps + contrib_apps

    # Remove duplicates while preserving order
    return list(dict.fromkeys(all_apps))


INSTALLED_APPS: list[str] = _get_installed_apps()


__all__: list[str] = ["INSTALLED_APPS"]
