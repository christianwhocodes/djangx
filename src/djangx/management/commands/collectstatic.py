from pathlib import Path
from typing import Any

from django.contrib.staticfiles.management.commands.collectstatic import (
    Command as CollectstaticCommand,
)

from ..settings import TAILWIND


class Command(CollectstaticCommand):
    """
    Custom collectstatic command that ignores the Tailwind CSS source file.
    """

    def set_options(self, **options: Any) -> None:
        """
        Override to add the Tailwind CSS source file to the ignore patterns.
        """
        super().set_options(**options)
        tailwind_conf = TAILWIND

        # Get the source CSS path
        source_css: Path = tailwind_conf.source
        source_css_dir = source_css.parent

        # Traverse up to find the 'static' directory
        while source_css_dir.name != "static" and source_css_dir != source_css_dir.parent:
            source_css_dir = source_css_dir.parent

        # Build the relative path from the static directory
        if source_css_dir.name == "static":
            # Get the relative path from static directory to the source file
            relative_path = source_css.relative_to(source_css_dir)
            ignore_pattern = str(relative_path)
        else:
            # Fallback: just ignore the filename
            ignore_pattern = source_css.name

        # Add to ignore patterns
        if self.ignore_patterns is None:
            self.ignore_patterns = []

        self.ignore_patterns.append(ignore_pattern)
