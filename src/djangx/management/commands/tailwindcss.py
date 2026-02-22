"""TailwindCSS CLI management command (install, build, watch, clean)."""

import stat
from pathlib import Path
from subprocess import DEVNULL, CalledProcessError, Popen, run
from threading import Event
from typing import Any

from christianwhocodes import Platform, Text, print
from django.core.management.base import BaseCommand, CommandError, CommandParser

from ... import PACKAGE
from ..settings import TAILWINDCSS


class _InstallHandler:
    """Handles the lifecycle of the TailwindCSS CLI binary.

    This includes platform detection, constructing download URLs, streaming the
    binary from GitHub, and managing local executable permissions.
    """

    _BASE_URL = "https://github.com/tailwindlabs/tailwindcss/releases"
    _PLATFORM_FILENAMES = {
        "windows": "tailwindcss-windows-x64.exe",
        "linux": "tailwindcss-linux-{arch}",
        "macos": "tailwindcss-macos-{arch}",
    }

    def __init__(self, verbose: bool = True) -> None:
        """Initialize the handler with system platform and settings."""
        self.verbose = verbose
        self.platform = Platform()
        self.version: str = TAILWINDCSS.version
        self.cli_path: Path = TAILWINDCSS.cli

    def install(self, skip_prompt: bool = False, use_cache: bool = False) -> None:
        """Execute the installation or update of the TailwindCSS CLI.

        Args:
            skip_prompt: If True, bypasses existence checks and forces a new download or redownload.
            use_cache: If True, prevents redownloading even if skip_prompt is requested.

        """
        exists = self.cli_path.exists() and self.cli_path.is_file()

        # Handle early exit if already installed
        if exists:
            if use_cache or not skip_prompt:
                if self.verbose:
                    print(f"✓ TailwindCSS CLI found at: {self.cli_path}", Text.SUCCESS)
                return

        # Prompt for confirmation if not in "force/skip_prompt" mode
        if not exists and not skip_prompt:
            if not self._prompt_confirmation():
                return

        self._ensure_directory()
        self._download(self._get_download_url())
        self._make_executable()

        if self.verbose:
            print("✓ Installation complete!", Text.SUCCESS)

    def _prompt_confirmation(self) -> bool:
        """Ask the user for permission to download the binary."""
        confirm = input(f"\nTailwindCSS CLI not found. Download version {self.version}? (y/N): ")
        if confirm.strip().lower() != "y":
            if self.verbose:
                print("❌ Installation cancelled.", Text.WARNING)
            return False
        return True

    def _ensure_directory(self) -> None:
        """Create the parent directory for the CLI if it doesn't exist."""
        try:
            self.cli_path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise CommandError(
                f"Permission denied: Cannot create directory at {self.cli_path.parent}"
            )

    def _get_download_url(self) -> str:
        """Construct the GitHub release URL based on platform and version."""
        filename = self._PLATFORM_FILENAMES.get(self.platform.os_name)
        if not filename:
            raise CommandError(f"Unsupported platform: {self.platform.os_name}")

        filename = filename.format(arch=self.platform.architecture)
        return f"{self._BASE_URL}/download/{self.version}/{filename}"

    def _download(self, url: str) -> None:
        """Stream the binary from GitHub to a temporary file, then move to destination.

        Args:
            url: The direct download link for the binary.

        """
        from urllib.error import HTTPError, URLError
        from urllib.request import Request, urlopen

        temp_destination = self.cli_path.with_suffix(self.cli_path.suffix + ".tmp")
        try:
            if self.verbose:
                print(f"\n📥 Downloading TailwindCSS CLI v{self.version}...", Text.INFO)

            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=15) as response, open(temp_destination, "wb") as out_file:
                total_size = int(response.info().get("Content-Length", 0))
                downloaded = 0
                while True:
                    buffer = response.read(8192)
                    if not buffer:
                        break
                    out_file.write(buffer)
                    downloaded += len(buffer)
                    if self.verbose and total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r   Progress: {percent:.1f}%", end="")

            if self.verbose:
                print("")
            temp_destination.rename(self.cli_path)
        except HTTPError as e:
            if temp_destination.exists():
                temp_destination.unlink()
            raise CommandError(f"Download failed (HTTP {e.code}): {e.reason}")
        except URLError as e:
            if temp_destination.exists():
                temp_destination.unlink()
            raise CommandError(f"Download failed (network error): {e.reason}")
        except Exception as e:
            if temp_destination.exists():
                temp_destination.unlink()
            raise CommandError(f"Download failed: {e}")

    def _make_executable(self) -> None:
        """Apply executable permissions to the binary on non-Windows systems."""
        if self.platform.os_name != "windows":
            current_perms = self.cli_path.stat().st_mode
            self.cli_path.chmod(current_perms | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


class _BaseHandler:
    """Abstract base class for running TailwindCSS CLI operations.

    Provides shared logic for validating the environment and constructing
    command-line arguments.
    """

    def __init__(self, verbose: bool = True) -> None:
        """Initialize with verbosity settings."""
        self.verbose = verbose
        self.cli_path: Path = TAILWINDCSS.cli
        self.source_css: Path = TAILWINDCSS.source
        self.output_css: Path = TAILWINDCSS.output
        self.tailwindcss_disabled: bool = TAILWINDCSS.disable

    def _validate_env(self) -> None:
        """Ensure the CLI exists and the source CSS file is present."""
        if not self.cli_path.exists():
            raise CommandError(f"CLI not found. Run '{PACKAGE.name} tailwindcss install' first.")
        if not self.source_css.exists():
            raise CommandError(f"Source CSS file not found at: {self.source_css}")

    def _get_base_args(self) -> list[str]:
        """Build the standard argument list for a TailwindCSS build."""
        return [
            str(self.cli_path),
            "-i",
            str(self.source_css),
            "-o",
            str(self.output_css),
            "--minify",
        ]


class BuildHandler(_BaseHandler):
    """Handles one-off compilation of TailwindCSS."""

    def build(self) -> bool:
        """Run the TailwindCSS build process.

        Args:
            skip_if_no_source: If True, silently skip when source CSS is missing.

        Returns:
            True if the build succeeded, False if skipped.

        """
        if self.tailwindcss_disabled:
            return False
        self._validate_env()
        args = self._get_base_args()
        try:
            if self.verbose:
                print("   Building TailwindCSS...", Text.INFO)

            run(args, check=True, stdout=DEVNULL, stderr=DEVNULL)

            if self.verbose:
                print("   ✓ Build complete!", Text.SUCCESS)
        except CalledProcessError as e:
            raise CommandError(f"Build failed: {e}")
        return True


class WatchHandler(_BaseHandler):
    """Handles the persistent TailwindCSS watcher process."""

    def __init__(self, verbose: bool = True) -> None:
        """Initialize the watch handler with process tracking."""
        super().__init__(verbose)
        self._process: Popen[bytes] | None = None

    def watch(self, stop_event: Event | None = None) -> None:
        """Start the TailwindCSS watcher.

        Args:
            stop_event: Optional threading.Event to signal process termination.
            skip_if_no_source: If True, silently skip when source CSS is missing.

        """
        if self.tailwindcss_disabled:
            return
        self._validate_env()
        args = self._get_base_args() + ["--watch"]
        try:
            if self.verbose:
                print("   Starting TailwindCSS watcher (Press Ctrl+C to stop)...", Text.INFO)

            # Streaming output to console so compiler errors are visible
            self._process = Popen(args)

            if stop_event:
                while self._process.poll() is None:
                    if stop_event.wait(timeout=0.5):
                        break
            else:
                self._process.wait()
        except KeyboardInterrupt:
            pass
        finally:
            if self._process:
                self._process.terminate()
                self._process.wait()


class CleanHandler(_BaseHandler):
    """Handles the removal of generated CSS artifacts."""

    def clean(self) -> None:
        """Delete the generated output CSS file if it exists."""
        if self.output_css.exists():
            self.output_css.unlink()
            if self.verbose:
                print(f"✓ Deleted generated output: {self.output_css}", Text.INFO)
        elif self.verbose:
            print("   No output file to clean.", Text.INFO)


class Command(BaseCommand):
    """TailwindCSS management command.

    Provides subcommands for installing the CLI, building assets,
    watching for changes, and cleaning up generated files.
    """

    help = "TailwindCSS CLI management: install, build, watch, and clean."

    def add_arguments(self, parser: CommandParser) -> None:
        """Define subcommands and their respective arguments."""
        subparsers = parser.add_subparsers(dest="command", required=True)

        # INSTALL: Supports -f/--force for redownloading
        install_parser = subparsers.add_parser("install", help="Install TailwindCSS CLI.")
        install_parser.add_argument(
            "-f",
            "--force",
            dest="skip_prompt",
            action="store_true",
            help="Force a new download or redownload and bypass confirmation prompts.",
        )
        install_parser.add_argument(
            "--use-cache", action="store_true", help="Skip download if CLI binary already exists."
        )

        subparsers.add_parser("build", help="Compile source CSS into minified output.")
        subparsers.add_parser("watch", help="Watch source files and rebuild on changes.")
        subparsers.add_parser("clean", help="Remove the generated output CSS file.")

    def handle(self, *args: Any, **options: Any) -> None:
        """Route the management command to the appropriate handler."""
        cmd = options["command"]
        v = options.get("verbosity", 1) > 0

        if cmd == "install":
            _InstallHandler(v).install(
                skip_prompt=options["skip_prompt"], use_cache=options["use_cache"]
            )
        elif cmd == "build":
            _: bool = BuildHandler(v).build()
        elif cmd == "watch":
            WatchHandler(v).watch()
        elif cmd == "clean":
            CleanHandler(v).clean()
