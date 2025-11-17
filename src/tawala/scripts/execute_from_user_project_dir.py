#!/usr/bin/env python

import os
import sys
from pathlib import Path


def main() -> None:
    sys.path.insert(0, str(Path.cwd()))
    _ = os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    try:
        from django.core.management import ManagementUtility
    except ImportError as exc:
        raise ImportError(
            (
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        ) from exc

    # Create the utility, set the custom program name, and execute
    utility = ManagementUtility(sys.argv)
    utility.prog_name = "tawala"
    utility.execute()


if __name__ == "__main__":
    main()
