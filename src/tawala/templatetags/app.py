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
            relative_path: Path to the asset relative to APP_DIR/static
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
_asset_resolver = StaticAssetResolver(settings.APP_DIR)


@register.simple_tag
def app_name() -> str:
    """Return the application name from settings.

    Returns:
        The application name
    """
    return settings.APP["NAME"]


@register.simple_tag
def app_short_name() -> str:
    """Return the application short name from settings.

    Returns:
        The application shortname
    """
    return settings.APP["SHORT_NAME"]


@register.simple_tag
def app_description() -> str:
    """Return the application description from settings.

    Returns:
        The application description
    """
    return settings.APP["DESCRIPTION"]


@register.simple_tag
def app_logo_url() -> str:
    """Return the application logo URL from settings.

    Returns:
        The application logo URL
    """
    return _asset_resolver.get_asset_url(
        relative_path="img/logo.png", fallback_path="defaults/logo.png"
    )


@register.simple_tag
def app_favicon_url() -> str:
    """Return the application favicon URL from settings.

    Returns:
        The application favicon URL
    """
    return _asset_resolver.get_asset_url(
        relative_path="img/favicon.ico", fallback_path="defaults/favicon.ico"
    )
