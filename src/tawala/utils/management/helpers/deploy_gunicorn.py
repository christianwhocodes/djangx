import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.core.management.base import CommandError

from .common import get_project_info

if TYPE_CHECKING:
    from django.core.management.base import BaseCommand

__all__ = [
    "check_gunicorn_deployment_option",
    "setup_gunicorn",
]


def check_gunicorn_deployment_option(
    command: "BaseCommand", options: dict[str, Any]
) -> None:
    """Checks if the --gunicorn deployment option is provided."""
    if not options["gunicorn"]:
        raise CommandError("Please specify a deployment method. Use --gunicorn")


def setup_gunicorn(command: "BaseCommand", options: dict[str, Any]) -> None:
    """
    Complete Gunicorn setup: configure socket and service.
    """
    _setup_gunicorn_socket(command)
    _setup_gunicorn_service(command, options)


def _setup_gunicorn_socket(command: "BaseCommand") -> None:
    """Creates and enables the Gunicorn systemd socket."""
    command.stdout.write(command.style.SUCCESS("\n→ Setting up Gunicorn socket..."))
    _, project_name = get_project_info()
    socket_path = Path(f"/etc/systemd/system/{project_name}.socket")

    socket_content = f"""[Unit]
Description=Gunicorn socket for {project_name}

[Socket]
ListenStream=/run/{project_name}.sock

[Install]
WantedBy=sockets.target
"""
    command.stdout.write(f"  Creating socket file: {socket_path}")
    socket_path.write_text(socket_content)

    subprocess.run(["systemctl", "start", f"{project_name}.socket"], check=True)
    subprocess.run(["systemctl", "enable", f"{project_name}.socket"], check=True)
    command.stdout.write(
        command.style.SUCCESS("  ✓ Gunicorn socket set up successfully")
    )


def _setup_gunicorn_service(command: "BaseCommand", options: dict[str, Any]) -> None:
    """Creates and enables the Gunicorn systemd service."""
    command.stdout.write(command.style.SUCCESS("\n→ Setting up Gunicorn service..."))
    project_root, project_name = get_project_info()
    wsgi_module = settings.WSGI_APPLICATION.rpartition(".")[0] + ":application"
    service_path = Path(f"/etc/systemd/system/{project_name}.service")

    service_content = f"""[Unit]
Description=Gunicorn daemon for {project_name}
Requires={project_name}.socket
After=network.target

[Service]
User={options["user"]}
Group={options["group"]}
WorkingDirectory={project_root}
ExecStart={sys.executable} -m gunicorn {wsgi_module} \\
          --access-logfile - \\
          --workers {options["workers"]} \\
          --bind unix:/run/{project_name}.sock

[Install]
WantedBy=multi-user.target
"""
    command.stdout.write(f"  Creating service file: {service_path}")
    service_path.write_text(service_content)

    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "restart", f"{project_name}.service"], check=True)
    subprocess.run(["systemctl", "enable", f"{project_name}.service"], check=True)

    command.stdout.write(
        command.style.SUCCESS("  ✓ Gunicorn service set up successfully")
    )
