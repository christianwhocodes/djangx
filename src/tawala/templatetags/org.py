from pathlib import Path

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


class StaticAssetResolver:
    """Resolver for static asset URLs with fallback support."""

    def __init__(self, app_dir: Path):
        """Initialize the resolver with the application directory.

        Args:
            app_dir: The application root directory
        """
        self.app_dir = app_dir

    def get_asset_url(self, relative_path: str, fallback_path: str) -> str:
        """Get the URL for a static asset.

        Args:
            relative_path: Path to the asset relative to app_dir/static
            fallback_path: Fallback path relative to static directory

        Returns:
            The static URL for the asset or fallback
        """
        expected_asset: Path = self.app_dir / "static" / relative_path

        if expected_asset.exists() and expected_asset.is_file():
            asset_dir: Path = expected_asset.parent

            # Traverse up to find the static directory
            while asset_dir.name != "static" and asset_dir != asset_dir.parent:
                asset_dir = asset_dir.parent

            relative_asset_path: Path = expected_asset.relative_to(asset_dir)
            return static(str(relative_asset_path))
        else:
            return static(fallback_path)


# Initialize the resolver
_asset_resolver = StaticAssetResolver(settings.PROJECT["dirs"]["APP"])


@register.simple_tag
def org_name() -> str:
    """Return the organization name from settings.

    Returns:
        The organization name
    """
    return settings.ORG["name"]


@register.simple_tag
def org_short_name() -> str:
    """Return the organization short name from settings.

    Returns:
        The organization shortname
    """
    return settings.ORG["short_name"]


@register.simple_tag
def org_description() -> str:
    """Return the organization description from settings.

    Returns:
        The organization description
    """
    return settings.ORG["description"]


@register.simple_tag
def org_logo_url() -> str:
    """Return the organization logo URL from settings.

    Returns:
        The organization logo URL
    """
    return _asset_resolver.get_asset_url(
        relative_path="app/global/logo.png", fallback_path=f"{settings.PKG['name']}/global/logo.png"
    )


@register.simple_tag
def org_favicon_url() -> str:
    """Return the organization favicon URL from settings.

    Returns:
        The organization favicon URL
    """
    return _asset_resolver.get_asset_url(
        relative_path="app/global/favicon.ico", fallback_path=f"{settings.PKG['name']}/global/favicon.ico"
    )


@register.simple_tag
def org_apple_touch_icon_url() -> str:
    """Return the organization Apple Touch Icon URL from settings.

    Returns:
        The organization Apple Touch Icon URL
    """
    return _asset_resolver.get_asset_url(
        relative_path="app/global/apple-touch-icon.png",
        fallback_path=f"{settings.PKG['name']}/global/apple-touch-icon.png",
    )
