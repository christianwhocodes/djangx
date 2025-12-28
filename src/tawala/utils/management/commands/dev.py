from socket import gaierror, gethostbyname, gethostname
from typing import Any

from django.conf import settings
from django.contrib.staticfiles.management.commands.runserver import (
    Command as RunserverCommand,
)
from django.core.management.base import CommandParser
from django.utils import timezone

from ..art import ArtPrinter


class Command(RunserverCommand):
    help = "Development server"

    # Declare parent class attributes for type checking
    _raw_ipv6: bool
    addr: str
    port: str
    protocol: str
    use_ipv6: bool
    no_clipboard: bool

    def add_arguments(self, parser: CommandParser) -> None:
        """Add custom arguments to the command.

        Extends the parent runserver arguments with specific options.

        Args:
            parser: The argument parser to add arguments to.
        """
        super().add_arguments(parser)
        parser.add_argument(
            "--no-clipboard",
            action="store_true",
            help="Disable copying the server URL to clipboard",
        )

    def handle(self, *args: object, **options: Any) -> str | None:
        """Handle the dev command execution.

        Processes command options and invokes the parent runserver command.

        Args:
            *args: Positional arguments from the command.
            **options: Command options including:
                - no_clipboard (bool): If True, skip clipboard copying.

        Returns:
            Result from parent command or None.
        """
        self.no_clipboard = options.get("no_clipboard", False)
        return super().handle(*args, **options)

    def check_migrations(self) -> None:
        f"""Check for unapplied migrations and display a warning.

        Overrides Django's default check_migrations to use '{settings.PKG_NAME} migrate'
        instead of 'python manage.py migrate' in the warning message.

        Prints a notice if there are unapplied migrations that could affect
        the project's functionality.
        """
        from django.core.exceptions import ImproperlyConfigured
        from django.db import DEFAULT_DB_ALIAS, connections
        from django.db.migrations.executor import MigrationExecutor

        try:
            executor = MigrationExecutor(connections[DEFAULT_DB_ALIAS])
        except ImproperlyConfigured:
            return

        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if plan:
            apps_waiting_migration = sorted(
                {migration.app_label for migration, backwards in plan}  # type: ignore[reportUnusedVariable]
            )
            self.stdout.write(
                self.style.NOTICE(
                    "\nYou have %(unapplied_migration_count)s unapplied migration(s). "
                    "Your project may not work properly until you apply the "
                    "migrations for app(s): %(apps_waiting_migration)s."
                    % {
                        "unapplied_migration_count": len(plan),
                        "apps_waiting_migration": ", ".join(apps_waiting_migration),
                    }
                )
            )
            OVERRIDE = f"{settings.PKG_NAME} migrate"  # Only thing we're overriding
            self.stdout.write(self.style.NOTICE(f"Run {OVERRIDE} to apply them."))

    def on_bind(self, server_port: int) -> None:
        """Custom server startup message and initialization.

        Overrides Django's default on_bind to provide a custom startup
        banner, server information, and clipboard functionality.
        Called when the development server binds to a port. Displays startup
        banner, server information, and optionally copies the URL to clipboard.

        Args:
            server_port: The port the server is bound to.
        """
        self._print_startup_message()
        self._print_startup_banner()
        self._print_server_info(server_port)

        if not self.no_clipboard:
            self._copy_to_clipboard(server_port)

        self.stdout.write("")  # spacing

    def _print_startup_message(self) -> None:
        """Print initial startup message."""
        self.stdout.write(self.style.SUCCESS("\n✨ Starting dev server...") + "\n")

    def _print_startup_banner(self) -> None:
        """Print ASCII banner based on terminal width.

        Displays either a full ASCII art banner or a compact version depending
        on whether the terminal is wide enough. Includes warning messages and
        control instructions appropriate for the terminal size.
        """
        printer = ArtPrinter(self)
        printer.print_dev_banner()

    def _print_server_info(self, server_port: int) -> None:
        """Print server and version information.

        Displays the current date/time with timezone, version,
        local server address, and network address (if applicable).

        Args:
            server_port: The port the server is bound to.
        """
        self._print_timestamp()
        self._print_version()
        self._print_local_url(server_port)

        if self.addr in ("0", "0.0.0.0"):
            self._print_network_url(server_port)

    def _print_timestamp(self) -> None:
        """Print current date and time with timezone."""
        tz = timezone.get_current_timezone()
        now = timezone.localtime(timezone.now(), timezone=tz)
        timestamp = now.strftime("%B %d, %Y - %X")
        tz_name = now.strftime("%Z")

        if tz_name:
            self.stdout.write(f"\n  📅 Date: {self.style.HTTP_NOT_MODIFIED(timestamp)} ({tz_name})")
        else:
            self.stdout.write(f"\n  📅 Date: {self.style.HTTP_NOT_MODIFIED(timestamp)}")

    def _print_version(self) -> None:
        """Print version."""

        self.stdout.write(
            f"  🔧 {settings.PKG_NAME.capitalize()} version: {self.style.HTTP_NOT_MODIFIED(settings.PKG_VERSION)}"
        )

    def _print_local_url(self, server_port: int) -> None:
        """Print local server URL.

        Args:
            server_port: The port the server is bound to.
        """
        addr = self._format_address()
        url = f"{self.protocol}://{addr}:{server_port}/"
        self.stdout.write(f"  🌐 Local address:   {self.style.SUCCESS(url)}")

    def _format_address(self) -> str:
        """Format address for display.

        Handles IPv6 addresses by wrapping them in brackets and formats
        0.0.0.0 for display.

        Returns:
            The formatted address string ready for display.
        """
        if self._raw_ipv6:
            return f"[{self.addr}]"
        elif self.addr == "0":
            return "0.0.0.0"
        else:
            return self.addr

    def _print_network_url(self, server_port: int) -> None:
        """Print LAN IP address if available.

        Attempts to determine the local network IP address and displays
        the network URL for accessing the dev server from other machines
        on the same network. Silently fails if the address cannot be determined.

        Args:
            server_port: The port the server is bound to.
        """
        try:
            hostname = gethostname()
            local_ip = gethostbyname(hostname)
            network_url = f"{self.protocol}://{local_ip}:{server_port}/"
            self.stdout.write(f"  🌍 Network address: {self.style.SUCCESS(network_url)}")
        except gaierror:
            pass

    def _copy_to_clipboard(self, server_port: int) -> None:
        """Copy server URL to clipboard.

        Attempts to copy the server URL to the system clipboard using pyperclip.
        Gracefully handles missing pyperclip or clipboard unavailability.

        Args:
            server_port: The port the server is bound to.
        """
        try:
            from pyperclip import copy

            addr = self._format_address()
            url = f"{self.protocol}://{addr}:{server_port}/"

            copy(url)
            self.stdout.write(f"  📋 {self.style.SUCCESS('Copied to clipboard!')}")
        except ImportError:
            self.stdout.write(
                f"  📋 {self.style.WARNING('pyperclip not installed - skipping clipboard copy')}"
            )
        except Exception:
            pass
