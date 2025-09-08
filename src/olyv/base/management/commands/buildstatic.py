from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Runs compilescss, collectstatic (ignoring *.scss), and compilescss --delete-files."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print the commands that would be run without executing them.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            print("Would run: compilescss")
            print("Would run: collectstatic --ignore=*.scss --noinput")
            print("Would run: compilescss --delete-files")
        else:
            call_command("compilescss")
            call_command("collectstatic", ignore=["*.scss"], interactive=False)
            call_command("compilescss", delete_files=True)
