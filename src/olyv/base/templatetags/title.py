from django import template
from django.conf import settings
from django.template import Context
from django.utils.safestring import SafeString, mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def title(context: Context, title: str | None = None, separator: str = " | ") -> SafeString:
    """
    Generate a complete HTML `<title>` tag combining page title and site name.

    Creates a properly formatted `<title>` element that combines a page-specific
    title with the site name from environment configuration. The title follows
    the pattern: "Page Title | Site Name" or just "Site Name" if no page title.

    Args:
        context: Django template context (automatically passed)
        title: Optional page title. If not provided, uses context['page_title']
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
    site_name = getattr(settings, "SITE_NAME", "").strip()
    title = title or context.get("page_title")

    full_title = f"{title}{separator}{site_name}" if title else site_name
    return mark_safe(f"<title>{full_title}</title>")
