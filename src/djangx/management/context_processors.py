"""Context processors."""

from django.http import HttpRequest

from .settings import TAILWINDCSS, TAILWINDCSS_OUTPUT_URL

# ============================================================================
# TailwindCSS Context Processor
# ============================================================================


def tailwindcss(request: HttpRequest) -> dict[str, dict[str, bool | str]]:
    """Add TailwindCSS settings to the template context."""
    return {
        "tailwindcss": {
            "is_disabled": TAILWINDCSS.is_disabled,
            "output_url": TAILWINDCSS_OUTPUT_URL,
        },
    }
