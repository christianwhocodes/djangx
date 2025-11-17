from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Creates a .env file with default environment variables"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force overwrite existing .env file without prompting",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable DEBUG mode",
        )
        parser.add_argument(
            "--allowed-hosts",
            default="localhost,127.0.0.1",
            help="Set ALLOWED_HOSTS value (default: localhost,127.0.0.1)",
        )
        parser.add_argument(
            "--db-backend",
            help="Set DB_BACKEND value (e.g., postgresql)",
        )
        parser.add_argument(
            "--pg-service",
            help="Set PG_SERVICE value (applicable if DB_BACKEND is postgresql)",
        )
        parser.add_argument(
            "--email-backend",
            help="Set EMAIL_BACKEND value (e.g., django.core.mail.backends.console.EmailBackend)",
        )
        parser.add_argument(
            "--email-host",
            help="Set EMAIL_HOST value",
        )
        parser.add_argument(
            "--email-host-user",
            help="Set EMAIL_HOST_USER value",
        )
        parser.add_argument(
            "--email-host-password",
            help="Set EMAIL_HOST_PASSWORD value",
        )

    def handle(self, *args, **options):
        # Determine the path for the .env file
        if hasattr(settings, "BASE_DIR"):
            env_file = Path(settings.BASE_DIR) / ".env"
        else:
            self.stdout.write(
                self.style.ERROR(
                    "BASE_DIR not found in settings. Cannot determine .env file location."
                )
            )
            return

        # Check if .env exists and has content
        if env_file.exists():
            content = env_file.read_text(encoding="utf-8").strip()
            if content and not options["force"]:
                response = input(
                    f"\n.env file already exists at {env_file} and contains data.\nDo you want to overwrite it? (y/N): "
                )
                if response.strip().lower() != "y":
                    self.stdout.write(self.style.WARNING("Operation cancelled."))
                    return

        # Validate PG_SERVICE applicability
        if options["pg_service"] and options.get("db_backend") != "postgresql":
            self.stdout.write(
                self.style.WARNING(
                    "PG_SERVICE is only applicable when DB_BACKEND is set to 'postgresql'. Ignoring PG_SERVICE."
                )
            )
            options["pg_service"] = None

        # Define environment variables using options
        env_content = f"""# 🚀 Core Django Configuration
DEBUG="{options["debug"]}"
ALLOWED_HOSTS="{options["allowed_hosts"]}"

# 🗄️ Database Configuration
"""
        if options["db_backend"]:
            env_content += f'DB_BACKEND="{options["db_backend"]}"\n'
        else:
            env_content += '# DB_BACKEND="postgresql"\n'
        if options["pg_service"]:
            env_content += f'PG_SERVICE="{options["pg_service"]}"\n'
        else:
            env_content += '# PG_SERVICE="Only set if DB_BACKEND is postgresql"\n'

        env_content += """
# 📧 Email Configuration
"""
        if options["email_backend"]:
            env_content += f'EMAIL_BACKEND="{options["email_backend"]}"\n'
        else:
            env_content += (
                '# EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend"\n'
            )
        if options["email_host"]:
            env_content += f'EMAIL_HOST="{options["email_host"]}"\n'
        else:
            env_content += '# EMAIL_HOST=""\n'
        if options["email_host_user"]:
            env_content += f'EMAIL_HOST_USER="{options["email_host_user"]}"\n'
        else:
            env_content += '# EMAIL_HOST_USER=""\n'
        if options["email_host_password"]:
            env_content += f'EMAIL_HOST_PASSWORD="{options["email_host_password"]}"\n'
        else:
            env_content += '# EMAIL_HOST_PASSWORD=""\n'

        try:
            # Write the .env file
            env_file.write_text(env_content, encoding="utf-8")
            self.stdout.write(
                self.style.SUCCESS(f"✅ Successfully created .env file at {env_file}")
            )
            self.stdout.write(
                self.style.WARNING(
                    "⚠️  Make sure to review and update sensitive values!"
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error creating .env file: {e}"))
