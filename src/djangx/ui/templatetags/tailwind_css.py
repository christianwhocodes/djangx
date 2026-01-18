from pathlib import Path

from django import template
from django.templatetags.static import static
from django.utils.safestring import SafeString

from ...settings import TAILWIND

register = template.Library()


@register.simple_tag
def tailwind_css() -> SafeString:
    """Return the Tailwind CSS link tag."""
    output_css: Path = TAILWIND.output

    if output_css.exists() and output_css.is_file():
        return SafeString(f'<link rel="stylesheet" href="{static("ui/css/tailwind.min.css")}">')
    return SafeString("")
