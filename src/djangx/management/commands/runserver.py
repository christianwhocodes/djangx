import signal
from threading import Event, Thread
from typing import Any, Optional

from django.contrib.staticfiles.management.commands.runserver import (
    Command as RunserverCommand,
)
from django.core.management.base import CommandParser

from ... import PACKAGE
from ..settings import TAILWIND
from .tailwind import BuildHandler, CleanHandler, WatchHandler


class Command(RunserverCommand):
    help = "Development server"

    # Declare parent class attributes for type checking
    _raw_ipv6: bool
    addr: str
    port: str
    protocol: str
    use_ipv6: bool
    no_clipboard: bool
    no_tailwind_watch: bool
    verbose: bool
    _watcher_thread: Optional[Thread]
    _stop_watcher_event: Optional[Event]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._watcher_thread = None
        self._stop_watcher_event = None
        self._original_sigint_handler = None
        self._shutdown_in_progress = False
        self.verbose = False

    def add_arguments(self, parser: CommandParser) -> None:
        """Add custom arguments to the command."""
        super().add_arguments(parser)
        parser.add_argument(
            "--no-clipboard",
            action="store_true",
            help="Disable copying the server URL to clipboard",
        )
        parser.add_argument(
            "--no-tailwind-watch",
            action="store_true",
            help="Disable Tailwind CSS file watching",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed Tailwind operations and status messages",
        )

    def handle(self, *args: object, **options: Any) -> Optional[str]:
        """Handle the dev command execution."""
        self.no_clipboard = options.get("no_clipboard", False)
        self.no_tailwind_watch = options.get("no_tailwind_watch", False)
        self.verbose = options.get("verbose", False)

        self._setup_signal_handlers()

        try:
            return super().handle(*args, **options)
        except KeyboardInterrupt:
            # Expected during shutdown - propagate after cleanup
            raise
        finally:
            # Ensure cleanup happens even if parent class has issues
            self._cleanup_watcher()

    def inner_run(self, *args: Any, **options: Any) -> None:
        """Run before the development server starts."""
        self._prepare_tailwind()
        return super().inner_run(*args, **options)  # pyright: ignore

    def check_migrations(self) -> None:
        """Check for unapplied migrations and display a warning."""
        from django.core.exceptions import ImproperlyConfigured
        from django.db import DEFAULT_DB_ALIAS, connections
        from django.db.migrations.executor import MigrationExecutor

        try:
            executor = MigrationExecutor(connections[DEFAULT_DB_ALIAS])
        except ImproperlyConfigured:
            return

        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if not plan:
            return

        apps_waiting_migration = sorted({migration.app_label for migration, _ in plan})
        self.stdout.write(
            self.style.NOTICE(
                f"\nYou have {len(plan)} unapplied migration(s). "
                f"Your project may not work properly until you apply the "
                f"migrations for app(s): {', '.join(apps_waiting_migration)}."
            )
        )
        self.stdout.write(self.style.NOTICE(f"Run {PACKAGE.name} migrate to apply them."))

    def on_bind(self, server_port: int) -> None:
        """Display server startup information."""
        self._print_startup_banner()
        self._print_server_info(server_port)

        if not self.no_clipboard:
            self._copy_to_clipboard(server_port)

        self.stdout.write("")

    # ========== Signal Handling ==========

    def _setup_signal_handlers(self) -> None:
        """Set up custom signal handlers for graceful shutdown."""
        self._original_sigint_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self._handle_shutdown_signal)
        signal.signal(signal.SIGTERM, self._handle_shutdown_signal)

    def _handle_shutdown_signal(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals (Ctrl+C, SIGTERM) with proper synchronization."""
        # If already shutting down, ignore subsequent signals to let cleanup finish
        if self._shutdown_in_progress:
            return

        self._shutdown_in_progress = True

        # Show shutdown message if verbose
        if self.verbose:
            self.stdout.write(self.style.WARNING("\n\n🛑 Shutting down gracefully..."))

        # Clean up watcher before restoring signal handler
        self._cleanup_watcher()

        # Restore original handler for any subsequent signals
        if self._original_sigint_handler:
            signal.signal(signal.SIGINT, self._original_sigint_handler)

        # Now propagate the interrupt
        raise KeyboardInterrupt

    def _cleanup_watcher(self) -> None:
        """Stop the Tailwind watcher thread gracefully."""
        if not self._watcher_thread or not self._watcher_thread.is_alive():
            return

        if self.verbose:
            self.stdout.write(self.style.WARNING("   ⏹ Stopping Tailwind watcher..."))

        # Signal the thread to stop
        if self._stop_watcher_event:
            self._stop_watcher_event.set()

        # Wait for thread to finish with timeout
        self._watcher_thread.join(timeout=3.0)

        if self._watcher_thread.is_alive():
            if self.verbose:
                self.stdout.write(
                    self.style.WARNING(
                        "   ⚠ Tailwind watcher did not stop in time (will be terminated)"
                    )
                )
        else:
            if self.verbose:
                self.stdout.write(self.style.SUCCESS("   ✓ Tailwind watcher stopped"))

        self._watcher_thread = None
        self._stop_watcher_event = None

    # ========== Tailwind Management ==========

    def _prepare_tailwind(self) -> None:
        """Prepare Tailwind CSS before starting the server."""
        # Check if Tailwind source exists
        tailwind_available = TAILWIND.source.exists() and TAILWIND.source.is_file()

        if self.verbose:
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(self.style.HTTP_INFO("TAILWIND PREPARATION"))
            self.stdout.write("=" * 60)

        # Clean old output
        CleanHandler(verbose=self.verbose).clean()

        if not tailwind_available:
            if self.verbose:
                self.stdout.write(
                    self.style.WARNING(f"⚠ Tailwind source not found at: {TAILWIND.source}")
                )
                self.stdout.write(self.style.NOTICE("  Skipping Tailwind CSS operations"))
                self.stdout.write("=" * 60 + "\n")
            return

        if self.verbose:
            self.stdout.write(self.style.SUCCESS(f"✓ Found Tailwind source: {TAILWIND.source}"))

        # Build initial CSS
        if self.verbose:
            self.stdout.write(self.style.HTTP_INFO("\n📦 Building Tailwind CSS..."))

        build_success = BuildHandler(verbose=self.verbose).build(skip_if_no_source=True)

        if build_success and self.verbose:
            self.stdout.write(self.style.SUCCESS(f"✓ Output saved to: {TAILWIND.output}"))

        # Start watcher if not disabled
        if not self.no_tailwind_watch:
            if self.verbose:
                self.stdout.write(self.style.HTTP_INFO("\n👀 Starting file watcher..."))

            self._start_watcher()

            if self.verbose:
                self.stdout.write(
                    self.style.SUCCESS("✓ Watching for changes in Tailwind source files")
                )
        else:
            if self.verbose:
                self.stdout.write(
                    self.style.NOTICE("\n⏭ Tailwind watch disabled (--no-tailwind-watch)")
                )

        if self.verbose:
            self.stdout.write("=" * 60 + "\n")

    def _start_watcher(self) -> None:
        """Start the Tailwind watcher thread."""
        self._stop_watcher_event = Event()

        def run_watcher() -> None:
            handler = WatchHandler(verbose=self.verbose)
            handler.watch(skip_if_no_source=True, stop_event=self._stop_watcher_event)

        self._watcher_thread = Thread(
            target=run_watcher,
            daemon=False,  # Non-daemon ensures proper cleanup before exit
            name="TailwindWatcher",
        )
        self._watcher_thread.start()

    # ========== Display Methods ==========

    def _print_startup_banner(self) -> None:
        """Print ASCII banner."""
        from .helpers.art import ArtPrinter

        ArtPrinter(self).print_dev_server_banner()

    def _print_server_info(self, server_port: int) -> None:
        """Print server and version information."""
        self._print_timestamp()
        self._print_version()
        self._print_local_url(server_port)

        if self.addr in ("0", "0.0.0.0"):
            self._print_network_url(server_port)

    def _print_timestamp(self) -> None:
        """Print current date and time with timezone."""
        from django.utils import timezone

        tz = timezone.get_current_timezone()
        now = timezone.localtime(timezone.now(), timezone=tz)
        timestamp = now.strftime("%B %d, %Y - %X")
        tz_name = now.strftime("%Z")

        date_display = f"\n  📅 Date: {self.style.HTTP_NOT_MODIFIED(timestamp)}"
        if tz_name:
            date_display += f" ({tz_name})"

        self.stdout.write(date_display)

    def _print_version(self) -> None:
        """Print version."""
        self.stdout.write(
            f"  🔧 {PACKAGE.display_name} version: {self.style.HTTP_NOT_MODIFIED(PACKAGE.version)}"
        )

    def _print_local_url(self, server_port: int) -> None:
        """Print local server URL."""
        url = f"{self.protocol}://{self._format_address()}:{server_port}/"
        self.stdout.write(f"  🌐 Local address:   {self.style.SUCCESS(url)}")

    def _format_address(self) -> str:
        """Format address for display."""
        if self._raw_ipv6:
            return f"[{self.addr}]"
        return "0.0.0.0" if self.addr == "0" else self.addr

    def _print_network_url(self, server_port: int) -> None:
        """Print LAN IP address if available."""
        from socket import gaierror, gethostbyname, gethostname

        try:
            hostname = gethostname()
            local_ip = gethostbyname(hostname)
            network_url = f"{self.protocol}://{local_ip}:{server_port}/"
            self.stdout.write(f"  🌍 Network address: {self.style.SUCCESS(network_url)}")
        except gaierror:
            pass

    def _copy_to_clipboard(self, server_port: int) -> None:
        """Copy server URL to clipboard."""
        try:
            from pyperclip import copy

            url = f"{self.protocol}://{self._format_address()}:{server_port}/"
            copy(url)
            self.stdout.write(f"  📋 {self.style.SUCCESS('Copied to clipboard!')}")
        except ImportError:
            self.stdout.write(
                f"  📋 {self.style.WARNING('pyperclip not installed - skipping clipboard copy')}"
            )
        except Exception:
            pass
