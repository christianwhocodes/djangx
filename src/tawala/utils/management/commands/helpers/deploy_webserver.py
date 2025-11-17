import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.core.management.base import CommandError

from .common import get_project_info

if TYPE_CHECKING:
    from django.core.management.base import BaseCommand

__all__ = ["check_webserver_conflicts", "setup_webserver"]


def check_webserver_conflicts(command: "BaseCommand", options: dict[str, Any]) -> None:
    """Checks for conflicting web server flags like --nginx and --skip-webserver."""
    webserver_flags = [options["nginx"], options["skip_webserver"]]
    if sum(webserver_flags) > 1:
        raise CommandError(
            "Cannot specify multiple web server options. Choose one: --nginx or --skip-webserver"
        )


def setup_webserver(command: "BaseCommand", options: dict[str, Any]) -> None:
    """
    Sets up the web server based on the provided options.

    If --nginx is specified, configures Nginx.
    If --skip-webserver is specified, skips configuration.
    Otherwise, prompts the user to choose.
    """
    if options["nginx"]:
        _setup_nginx(command, options)
    elif options["skip_webserver"]:
        command.stdout.write(
            command.style.WARNING("\nSkipping web server configuration")
        )
    else:
        _prompt_web_server(command, options)


def _prompt_web_server(command: "BaseCommand", options: dict[str, Any]) -> None:
    """Prompts the user to choose a web server configuration if not specified."""
    command.stdout.write("\n" + "=" * 60)
    command.stdout.write("Would you like to configure a web server?")
    command.stdout.write("=" * 60)
    command.stdout.write("1. Nginx")
    command.stdout.write("2. Skip")

    choice = input("\nEnter your choice (1-2): ").strip()
    match choice:
        case "1":
            _setup_nginx(command, options)
        case _:
            command.stdout.write(
                command.style.WARNING("Skipping web server configuration")
            )


def _setup_nginx(command: "BaseCommand", options: dict[str, Any]) -> None:
    """Creates and enables the Nginx site configuration."""
    command.stdout.write(command.style.SUCCESS("\n→ Deploying Nginx..."))
    _, project_name = get_project_info()

    server_name = " ".join(options["domain"]) if options.get("domain") else "_"
    command.stdout.write(f"  Using server name(s): {server_name}")

    nginx_config = f"""server {{
    listen 80;
    listen [::]:80;
    server_name {server_name};

    location /{settings.STATIC_URL.strip("/")}/ {{
        alias {settings.STATIC_ROOT}/;
    }}

    location /{settings.MEDIA_URL.strip("/")}/ {{
        alias {settings.MEDIA_ROOT}/;
    }}

    location / {{
        include proxy_params;
        proxy_pass http://unix:/run/{project_name}.sock;
    }}
}}
"""
    nginx_available = Path(f"/etc/nginx/sites-available/{project_name}")
    nginx_enabled = Path(f"/etc/nginx/sites-enabled/{project_name}")

    command.stdout.write(f"  Creating Nginx config: {nginx_available}")
    nginx_available.write_text(nginx_config)

    if nginx_enabled.is_symlink() or nginx_enabled.exists():
        command.stdout.write(f"  Removing existing Nginx link: {nginx_enabled}")
        nginx_enabled.unlink()

    command.stdout.write(f"  Creating Nginx symlink: {nginx_enabled}")
    nginx_enabled.symlink_to(nginx_available)

    subprocess.run(["nginx", "-t"], check=True)
    subprocess.run(["systemctl", "reload", "nginx"], check=True)
    command.stdout.write(command.style.SUCCESS("  ✓ Nginx deployed successfully"))
