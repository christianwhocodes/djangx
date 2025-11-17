import os
from pathlib import Path
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.management.base import CommandError

if TYPE_CHECKING:
    from django.core.management.base import BaseCommand

__all__ = ["check_sudo_privileges", "get_project_info"]


def check_sudo_privileges(command: "BaseCommand") -> None:
    """Checks if the script is run with sudo/root privileges."""
    if os.geteuid() != 0:  # type: ignore[reportAttributeAccessIssue]
        command.stdout.write(
            command.style.ERROR("✗ This command requires root/sudo privileges.")
        )
        command.stdout.write(
            "  Please run with: sudo python manage.py deploy --gunicorn"
        )
        raise CommandError("Insufficient privileges")


def get_project_info() -> tuple[Path, str]:
    """Gets common project information: the root directory and project name."""
    project_root = Path(settings.BASE_DIR)
    project_name = project_root.name
    return project_root, project_name
