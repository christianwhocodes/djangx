from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key


class Command(BaseCommand):
    help = "Creates a .env file with default environment variables"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force overwrite existing .env file without prompting",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without actually creating the file",
        )

    def handle(self, *args, **options):
        # Get the project root using Django's BASE_DIR setting
        env_file = Path(settings.BASE_DIR) / ".env"

        # Dry run mode
        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN MODE - No files will be created"))
            self.stdout.write(f"Would create .env file at: {env_file}")

            if env_file.exists():
                content = env_file.read_text().strip()
                if content:
                    self.stdout.write(
                        self.style.WARNING(
                            "File exists and contains data - would prompt for overwrite"
                        )
                    )
                else:
                    self.stdout.write("File exists but is empty - would overwrite")
            else:
                self.stdout.write("File does not exist - would create new file")

            self.stdout.write("Would generate new SECRET_KEY and write environment variables")
            return

        # Check if .env exists and has content
        if env_file.exists():
            content = env_file.read_text().strip()
            if content and not options["force"]:
                response = input(
                    f"\n.env file already exists at {env_file} and contains data.\nDo you want to overwrite it? (y/N): "
                )
                if response.lower() != "y":
                    self.stdout.write(self.style.WARNING("Operation cancelled."))
                    return

        # Generate a random secret key using Django's utility
        secret_key = get_random_secret_key()

        # Define environment variables
        env_content = f"""# 🚀 Core Django Configuration
ROOT_URLCONF="settings.olyv.urls"
ENVIRONMENT="development"
SECRET_KEY="{secret_key}"
ALLOWED_HOSTS="localhost,127.0.0.1"

# 🗄️ Database Configuration
# DB_BACKEND="sqlite3"
# DB_NAME=""
# DB_USER="postgres"
# DB_PASSWORD="postgres"
# DB_HOST="localhost"
# DB_PORT="5432"

# 📧 Email Configuration
# EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend"
# EMAIL_HOST=""
# EMAIL_HOST_USER=""
# EMAIL_HOST_PASSWORD=""

# 🌐 Site Configuration
# SITE_URL="https://preview.bigpen.co.ke"
# SITE_NAME="Online BigPen Kenya"
# SITE_SHORT_NAME="BigPen"
# SITE_DESCRIPTION="Delivering Stationery Supplies"
# SITE_THEME_COLOR="#ef4444"
# SITE_KEYWORDS="bigpen,Online BigPen Kenya,ecommerce"
# SITE_AUTHOR="christianwhocodes"
# SITE_AUTHOR_URL="https://github.com/christianwhocodes/"
# SITE_NAVIGATION_TYPE="navbar"

# 🖼️ Site Assets
# SITE_LOGO="/lib/static/olyv/img/logo.png"
# SITE_FAVICON="/lib/static/olyv/img/favicon.ico"
# SITE_APPLE_TOUCH_ICON="/lib/static/olyv/img/apple-touch-icon.png"
# SITE_ANDROID_CHROME_ICON="/lib/static/olyv/img/android-chrome-icon.png"
# SITE_MSTILE="/lib/static/olyv/img/mstile.png"
# SITE_HERO="/lib/static/olyv/img/hero.jpg"
# SITE_MANIFEST="/lib/static/olyv/manifest.webmanifest"
"""

        try:
            # Write the .env file
            env_file.write_text(env_content)
            self.stdout.write(self.style.SUCCESS(f"✅ Successfully created .env file at {env_file}"))
            self.stdout.write(
                self.style.WARNING(
                    "⚠️  Make sure to review and update the SECRET_KEY and other sensitive values!"
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error creating .env file: {e}"))
