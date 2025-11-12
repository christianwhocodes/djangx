import os
import subprocess
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from ..utils.management.helpers.common import check_sudo_privileges
from ..utils.management.helpers.deploy_database import setup_database
from ..utils.management.helpers.deploy_gunicorn import (
    check_gunicorn_deployment_option,
    setup_gunicorn,
)
from ..utils.management.helpers.deploy_webserver import (
    check_webserver_conflicts,
    setup_webserver,
)


class Command(BaseCommand):
    """
    Deploys the Django application on a Linux server using Gunicorn and Nginx.

    This command automates the setup of systemd services for Gunicorn and a
    reverse proxy configuration for Nginx. It is designed to be run with sudo
    privileges as it writes files to `/etc/systemd/system/` and `/etc/nginx/`.

    Prerequisites:
    - A Linux-based operating system.
    - Gunicorn and Nginx must be installed on the system.
    - The command must be run with sudo/root privileges.

    Usage Examples:
    -----------------

    1. Basic deployment with Gunicorn (prompts for Nginx setup):
       $ sudo python manage.py deploy --gunicorn

    2. Deploy with Gunicorn and automatically configure Nginx for a domain:
       $ sudo python manage.py deploy --gunicorn --nginx --domain example.com www.example.com

    3. Deploy with Gunicorn but skip web server configuration entirely:
       $ sudo python manage.py deploy --gunicorn --skip-webserver

    4. Specify the number of Gunicorn workers (e.g., for a multi-core server):
       $ sudo python manage.py deploy --gunicorn --nginx --workers 5

    5. Specify a custom user and group for running the Gunicorn service:
       $ sudo python manage.py deploy --gunicorn --nginx --user myuser --group mygroup
    """

    help = "Deploy Django application on Linux using Gunicorn with optional Nginx configuration"

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Adds command-line arguments to the command."""
        parser.add_argument(
            "--gunicorn", action="store_true", help="Deploy with Gunicorn"
        )
        parser.add_argument(
            "--nginx",
            action="store_true",
            help="Configure Nginx (optional, prompts if not specified)",
        )
        parser.add_argument(
            "--skip-webserver",
            action="store_true",
            help="Skip web server configuration (optional, prompts if not specified)",
        )
        parser.add_argument(
            "--workers",
            type=int,
            default=3,
            help="Number of Gunicorn workers (default: 3)",
        )
        parser.add_argument(
            "--domain",
            nargs="+",
            help="Domain name(s) for the server (e.g., example.com www.example.com). If not provided, uses catch-all (_)",
        )
        parser.add_argument(
            "--user",
            type=str,
            default="www-data",
            help="User to run the Gunicorn service (default: www-data)",
        )
        parser.add_argument(
            "--group",
            type=str,
            default="www-data",
            help="Group to run the Gunicorn service (default: www-data)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """The main entry point for the management command."""
        match sys.platform:
            case "linux":
                check_sudo_privileges(self)
                check_gunicorn_deployment_option(self, options)
                check_webserver_conflicts(self, options)

                try:
                    setup_database(self)
                    setup_gunicorn(self, options)
                    setup_webserver(self, options)

                    self.stdout.write(
                        self.style.SUCCESS("\n✓ Deployment completed successfully")
                    )

                except subprocess.CalledProcessError as e:
                    self.stderr.write(
                        self.style.ERROR(f"A subprocess failed: {e.stderr}")
                    )
                    raise CommandError(f"Deployment failed: {e}") from e
            case "win32":
                raise CommandError(
                    "This command is not supported on Windows. Please use Windows Subsystem for Linux (WSL)."
                )
            case "darwin":
                raise CommandError("This command is not supported on macOS.")
            case _:
                raise CommandError(f"Unsupported operating system: {sys.platform}")


# ============================================================================
# TESTING BLOCK - Only runs when executed directly
# ============================================================================
if __name__ == "__main__":
    """
    Test individual methods from this management command.
    """
    import django

    # Add project root to Python path
    # This file is at: tawala/utils/management/commands/deploy.py
    # Project root is 5 levels up
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    # Setup Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()

    # Now create command instance
    cmd = Command()

    print("=" * 70)
    print("TESTING: Database setup methods")
    print("=" * 70)

    try:
        setup_database(cmd)

        print("\n" + "=" * 70)
        print("✓ TEST PASSED: Database setup methods completed successfully")
        print("=" * 70)
    except CommandError as e:
        print("\n" + "=" * 70)
        print(f"✗ TEST FAILED: {e}")
        print("=" * 70)
        sys.exit(1)
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"✗ UNEXPECTED ERROR: {e}")
        print("=" * 70)
        import traceback

        traceback.print_exc()
        sys.exit(1)
