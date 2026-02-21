"""Tailwind CSS template tag."""

from django.template import Library
from django.utils.safestring import SafeString

register = Library()


@register.simple_tag
def tailwind_css() -> SafeString:
    """Render the Tailwind CSS link tag if the output file exists."""
    from pathlib import Path

    from django.conf import settings
    from django.templatetags.static import static

    output_css: Path = settings.TAILWIND.output

    if output_css.exists() and output_css.is_file():
        return SafeString(
            f'<link rel="stylesheet" href="{static(settings.TAILWIND_OUTPUT_STATIC_URL)}">'
        )
    return SafeString("")
