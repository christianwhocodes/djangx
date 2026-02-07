from django.template import Library
from django.utils.safestring import SafeString

register = Library()


@register.simple_tag
def tailwind_css() -> SafeString:
    """
    Inbuilt template tag to include Tailwind CSS in templates.
    Checks if the Tailwind CSS file exists before rendering the link tag.

    Return the Tailwind CSS link tag.
    """
    from pathlib import Path

    from django.conf import settings
    from django.templatetags.static import static

    output_css: Path = settings.TAILWIND.output

    if output_css.exists() and output_css.is_file():
        return SafeString(
            f'<link rel="stylesheet" href="{static(settings.TAILWIND_OUTPUT_STATIC_URL)}">'
        )
    return SafeString("")
