"""Custom collectstatic command."""

from typing import Any

from django.contrib.staticfiles.management.commands.collectstatic import (
    Command as CollectstaticCommand,
)


class Command(CollectstaticCommand):
    """Custom collectstatic command that ignores the Tailwind CSS source file."""

    def set_options(self, **options: Any) -> None:
        """Override to add the Tailwind CSS source file to the ignore patterns."""
        from ..settings import TAILWIND_SOURCE_STATIC_URL

        super().set_options(**options)

        if self.ignore_patterns is None:
            self.ignore_patterns = []

        self.ignore_patterns.append(TAILWIND_SOURCE_STATIC_URL)
