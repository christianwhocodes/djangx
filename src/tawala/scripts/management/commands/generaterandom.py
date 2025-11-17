from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key


class Command(BaseCommand):
    help = "Generate a random string (can be used for Django SECRET_KEY)."
    requires_system_checks = []  # type: ignore[assignment]

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-clipboard",
            action="store_true",
            help="Skip copying the generated string to clipboard",
            default=False,
        )

    def handle(self, *args, **options):
        random_str = get_random_secret_key()
        self.stdout.write("Generated random string: " + self.style.SUCCESS(random_str))

        if not options["no_clipboard"]:
            try:
                import pyperclip

                pyperclip.copy(random_str)
                self.stdout.write(
                    self.style.SUCCESS("Copied to clipboard successfully.")
                )
            except ImportError:
                self.stdout.write(
                    self.style.ERROR(
                        "pyperclip is not installed. Install it to enable clipboard functionality (uv add pyperclip)."
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"Could not copy to clipboard: {e}")
                )
