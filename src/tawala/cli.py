#!/usr/bin/env python

import os
import sys

from django.conf import settings

# Configure Django settings
if not settings.configured:
    settings.configure(INSTALLED_APPS=["tawala.scripts"])


def main() -> None:
    _ = os.environ.setdefault("DJANGO_SETTINGS_MODULE", __name__)

    try:
        import django
        from django.core.management import ManagementUtility
    except ImportError as exc:
        raise ImportError(
            (
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        ) from exc

    django.setup()

    # Create the utility, set the custom program name, and execute
    utility = ManagementUtility(sys.argv)
    utility.prog_name = "tawala"
    utility.execute()


if __name__ == "__main__":
    main()
