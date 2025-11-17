import subprocess
from pathlib import Path
from shutil import which
from typing import TYPE_CHECKING, Any

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import DEFAULT_DB_ALIAS, connections

if TYPE_CHECKING:
    from django.core.management.base import BaseCommand

__all__ = ["setup_database"]


def setup_database(command: "BaseCommand") -> None:
    """
    Complete database setup: check engine, create database, run migrations and seed.
    """
    command.stdout.write(command.style.SUCCESS("\n→ Setting up database..."))

    db_conn = connections[DEFAULT_DB_ALIAS]
    db_settings = db_conn.settings_dict
    db_engine = db_settings["ENGINE"]
    db_options = db_settings.get("OPTIONS") or {}

    _check_db_engine(command, db_engine)
    _setup_db(command, db_engine, db_options)
    _run_migrations_and_seed(command)


def _check_db_engine(command: "BaseCommand", db_engine: str) -> None:
    """
    Checks for and installs the required database engine if it's missing.
    """
    command.stdout.write(command.style.SUCCESS("\n→ Checking database engine..."))
    match db_engine:
        case "django.db.backends.postgresql":
            if not which("psql"):
                command.stdout.write(
                    command.style.WARNING("  PostgreSQL not found. Installing...")
                )
                try:
                    subprocess.run(
                        ["apt", "update"],
                        check=True,
                        capture_output=True,
                    )
                    subprocess.run(
                        [
                            "apt",
                            "install",
                            "-y",
                            "postgresql",
                            "postgresql-contrib",
                            "libpq-dev",
                        ],
                        check=True,
                        capture_output=True,
                    )
                    subprocess.run(
                        ["systemctl", "enable", "--now", "postgresql"],
                        check=True,
                        capture_output=True,
                    )
                    command.stdout.write(
                        command.style.SUCCESS("✓ PostgreSQL installed and enabled.")
                    )
                except subprocess.CalledProcessError as e:
                    command.stderr.write(
                        command.style.ERROR(
                            f"Failed to install PostgreSQL: {e.stderr.decode()}"
                        )
                    )
                    raise CommandError("PostgreSQL installation failed.") from e
        case "django.db.backends.sqlite3":
            pass  # SQLite is ready (built-in).
        case _:
            command.stdout.write(
                command.style.WARNING(f"  Skipping engine check for: {db_engine}")
            )


def _setup_db(
    command: "BaseCommand", db_engine: str, db_options: dict[str, Any]
) -> None:
    """
    Creates the project database if it doesn't already exist.
    """
    command.stdout.write(command.style.SUCCESS("\n→ Setting up project database..."))
    match db_engine:
        case "django.db.backends.postgresql":
            if "service" in db_options:
                try:
                    service_name = db_options["service"]

                    # Service file paths
                    service_file_paths = [
                        Path.home() / ".pg_service.conf",
                        Path("/etc/postgresql-common/pg_service.conf"),
                    ]

                    # Find and read the service file
                    service_config = {}
                    for service_file in service_file_paths:
                        if service_file.exists():
                            current_service = None
                            with open(service_file, "r") as f:
                                for line in f:
                                    line = line.strip()
                                    if not line or line.startswith("#"):
                                        continue
                                    if line.startswith("[") and line.endswith("]"):
                                        current_service = line[1:-1]
                                    elif (
                                        current_service == service_name and "=" in line
                                    ):
                                        key, value = line.split("=", 1)
                                        service_config[key.strip()] = value.strip()
                            if service_config:
                                break

                    if not service_config:
                        raise CommandError(
                            f"Service '{service_name}' not found in any pg_service.conf file."
                        )

                    db_name = service_config.get("dbname")
                    user = service_config.get("user")

                    if not db_name or not user:
                        raise CommandError(
                            "Service config must contain 'dbname' and 'user'."
                        )

                    # Check if database exists
                    check_command = [
                        "psql",
                        "-U",
                        user,
                        "-d",
                        "postgres",
                        "-tc",
                        f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'",
                    ]
                    result = subprocess.run(
                        check_command, capture_output=True, text=True
                    )

                    if "1" in result.stdout.strip():
                        command.stdout.write(
                            command.style.SUCCESS(
                                f"✓ Database '{db_name}' already exists."
                            )
                        )
                    else:
                        command.stdout.write(
                            f"  Database '{db_name}' not found. Creating..."
                        )
                        create_command = ["createdb", "-U", user, db_name]
                        subprocess.run(
                            create_command,
                            check=True,
                            capture_output=True,
                            text=True,
                        )
                        command.stdout.write(
                            command.style.SUCCESS(f"✓ Database '{db_name}' created.")
                        )

                except Exception as e:
                    command.stderr.write(
                        command.style.ERROR(
                            f"Failed to create PostgreSQL database: {e}"
                        )
                    )
                    raise CommandError("PostgreSQL database setup failed.") from e
            else:
                command.stdout.write(
                    command.style.WARNING(
                        "  PostgreSQL connection is not using a service file. Skipping database creation."
                    )
                )
        case "django.db.backends.sqlite3":
            pass  # SQLite database file is created automatically
        case _:
            command.stdout.write(
                command.style.WARNING(f"  Skipping DB setup for: {db_engine}")
            )


def _run_migrations_and_seed(command: "BaseCommand") -> None:
    """
    Runs database migrations and seeds the database.
    """
    command.stdout.write(
        command.style.SUCCESS("\n→ Running migrations and seeding data...")
    )
    try:
        call_command("makemigrations")
        call_command("migrate")
        call_command("seed")
        command.stdout.write(
            command.style.SUCCESS("✓ Migrations and seeding completed successfully.")
        )
    except Exception as e:
        command.stderr.write(command.style.ERROR(f"An error occurred: {e}"))
        raise CommandError("Migrations or seeding failed.") from e
