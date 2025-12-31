from typing import Any

from django.conf import settings
from django.template import Library
from django.utils.html import format_html
from django.utils.safestring import SafeString

register = Library()


@register.simple_tag
def social_media_links() -> dict[str, dict[str, str]]:
    """
    Returns the complete social media configuration dictionary.

    Usage: {% social_media_links as social_links %}
    """
    return settings.SOCIAL_MEDIA


@register.simple_tag
def social_media_url(platform: str) -> str:
    """
    Get the URL for a specific social media platform.

    Usage: {% social_media_url 'facebook' %}
    """
    platform_config = settings.SOCIAL_MEDIA.get(platform, {})
    return platform_config.get("URL", "")


@register.simple_tag
def social_media_icon(platform: str) -> str:
    """
    Get the icon class for a specific social media platform.

    Usage: {% social_media_icon 'facebook' %}
    """
    platform_config = settings.SOCIAL_MEDIA.get(platform, {})
    return platform_config.get("ICON", "")


@register.simple_tag
def has_social_media(platform: str | None = None) -> bool:
    """
    Check if social media is configured.

    If platform is specified, checks if that specific platform is configured.
    If platform is None, checks if any social media platform is configured.

    Usage:
        {% has_social_media %}  # Returns True if any platform configured
        {% has_social_media 'facebook' %}  # Returns True if Facebook configured
    """
    if platform is None:
        return bool(settings.SOCIAL_MEDIA)
    return platform in settings.SOCIAL_MEDIA


@register.simple_tag
def social_media_count() -> int:
    """
    Returns the number of configured social media platforms.

    Usage: {% social_media_count %}
    """
    return len(settings.SOCIAL_MEDIA)


@register.inclusion_tag("social_media/links.html")
def render_social_media_links(css_class: str = "social-links") -> dict[str, Any]:
    """
    Renders social media links using a template.

    Usage: {% render_social_media_links %}
           {% render_social_media_links css_class="my-custom-class" %}
    """
    return {
        "social_media": settings.SOCIAL_MEDIA,
        "css_class": css_class,
    }


@register.simple_tag
def social_media_link_html(
    platform: str,
    link_text: str = "",
    css_class: str = "social-link",
    show_icon: bool = True,
    target: str = "_blank",
    rel: str = "noopener noreferrer",
) -> SafeString:
    """
    Generate HTML for a single social media link.

    Usage:
        {% social_media_link_html 'facebook' %}
        {% social_media_link_html 'twitter_x' link_text='Follow us' %}
        {% social_media_link_html 'instagram' show_icon=False %}
    """
    platform_config = settings.SOCIAL_MEDIA.get(platform)

    if not platform_config:
        return format_html("")

    url = platform_config.get("URL", "")
    icon = platform_config.get("ICON", "")

    if not url:
        return format_html("")

    # Build icon HTML
    icon_html = format_html('<i class="{}"></i> ', icon) if show_icon and icon else ""

    # Build link text
    display_text = link_text if link_text else platform.replace("_", " ").title()

    return format_html(
        '<a href="{}" class="{}" target="{}" rel="{}">{}{}</a>',
        url,
        css_class,
        target,
        rel,
        icon_html,
        display_text,
    )


@register.filter
def get_platform_config(
    social_media_dict: dict[str, dict[str, str]], platform: str
) -> dict[str, str]:
    """
    Get configuration for a specific platform from the social media dictionary.

    Usage: {{ SOCIAL_MEDIA|get_platform_config:'facebook' }}
    """
    return social_media_dict.get(platform, {})


@register.filter
def platform_exists(social_media_dict: dict[str, dict[str, str]], platform: str) -> bool:
    """
    Check if a platform exists in the social media configuration.

    Usage: {% if SOCIAL_MEDIA|platform_exists:'facebook' %}
    """
    return platform in social_media_dict
