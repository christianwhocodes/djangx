from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a hashed password for use in fixtures"

    def add_arguments(self, parser):
        parser.add_argument(
            "password", type=str, help="The plain text password to hash"
        )

    def handle(self, *args, **options):
        password = options["password"]
        hashed_password = make_password(password)
        self.stdout.write(self.style.SUCCESS(f"Hashed password: {hashed_password}"))
