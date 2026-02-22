"""Custom collectstatic command."""

from typing import Any

from django.contrib.staticfiles.management.commands.collectstatic import (
    Command as CollectstaticCommand,
)


class Command(CollectstaticCommand):
    """Collectstatic that ignores the TailwindCSS source file."""

    def set_options(self, **options: Any) -> None:
        """Add TailwindCSS source file to ignore patterns."""
        from ..settings import TAILWINDCSS, TAILWINDCSS_SOURCE_URL

        super().set_options(**options)

        if not TAILWINDCSS.is_disabled:
            if self.ignore_patterns is None:
                self.ignore_patterns = []

            self.ignore_patterns.append(TAILWINDCSS_SOURCE_URL)
