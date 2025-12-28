from pathlib import Path

from django import template
from django.conf import settings
from django.template import Context
from django.templatetags.static import static
from django.utils.safestring import SafeString, mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def title(context: Context, name: str | None = None, separator: str = " | ") -> SafeString:
    """
    Generate a complete HTML `<title>` tag combining page title and site name.

    Creates a properly formatted `<title>` element that combines a page-specific
    title with the site name from environment configuration. The title follows
    the pattern: "Page Title | Site Name" or just "Site Name" if no page title.

    Args:
        context: Django template context (automatically passed)
        name: Optional page title. If not provided, uses context['title']
        separator: String to separate page title and site name (default: " | ")

    Returns:
        SafeString containing the complete HTML `<title>` tag

    Usage:
        {% title %}                        ← "Site Name" or "Page Title | Site Name"
        {% title "Custom Page" %}          ← "Custom Page | Site Name"
        {% title "Custom Page" " - " %}    ← "Custom Page - Site Name"
        {% title separator=" :: " %}       ← "Page Title :: Site Name"

    Note:
        Requires SITE_NAME setting to be set for the site name portion.
    """
    site_name = ""
    title = name or context.get("title")

    full_title = f"{title}{separator if site_name else ''}{site_name}" if title else site_name
    return mark_safe(f"<title>{full_title}</title>")


@register.simple_tag
def tailwindcss() -> SafeString:
    output_css: Path = settings.TAILWINDCSS["OUTPUT"]
    output_static_dir = output_css.parent

    while output_static_dir.name != "static" and output_static_dir != output_static_dir.parent:
        output_static_dir = output_static_dir.parent

    relative_path = output_css.relative_to(output_static_dir)
    static_url = static(str(relative_path))

    return mark_safe(f"<link rel='stylesheet' href='{static_url}' />")
