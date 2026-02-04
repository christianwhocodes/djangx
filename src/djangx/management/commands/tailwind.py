"""
Management command for Tailwind CLI installation and build management.

This module provides a clean, OOP-based interface for:
- Installing the Tailwind CLI binary
- Building Tailwind output files
- Watching Tailwind source files for changes
- Cleaning generated CSS files
"""

from pathlib import Path
from subprocess import DEVNULL, CalledProcessError, Popen, run
from threading import Event
from typing import Any, Callable

from christianwhocodes.utils import PlatformInfo, Text, print
from django.core.management.base import BaseCommand, CommandError, CommandParser

from ... import PKG_NAME
from ..settings import TAILWIND


class TailwindValidator:
    """Shared validator for Tailwind CLI operations."""

    def __init__(self, verbose: bool = True) -> None:
        self.verbose = verbose

    def validate_cli_exists(self, cli_path: Path) -> None:
        """Validate that the Tailwind CLI exists."""
        if not cli_path.exists():
            raise CommandError(
                f"Tailwind CLI not found at '{cli_path}'. Run '{PKG_NAME} tailwind install' first."
            )

    def validate_source_file(self, source_css: Path, required: bool = True) -> bool:
        """Validate that the source CSS file exists.

        Returns:
            True if file exists and is valid, False otherwise.
        """
        if source_css.exists() and source_css.is_file():
            return True

        if required:
            raise CommandError(f"Tailwind source css file not found: {source_css}")

        if self.verbose:
            print(
                f"⚠ Tailwind source file not found: {source_css}",
                Text.WARNING,
            )
            print("  Skipping Tailwind operations.", Text.WARNING)
        return False

    def ensure_directory(self, directory: Path) -> None:
        """Ensure a directory exists with proper error handling."""
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise CommandError(
                f"Permission denied: Cannot create directory at {directory}. "
                "Ensure the path is writable."
            )


class TailwindDownloader:
    """Handles downloading and installation of Tailwind CLI."""

    BASE_URL = "https://github.com/tailwindlabs/tailwindcss/releases"
    PLATFORM_FILENAMES = {
        "windows": "tailwindcss-windows-x64.exe",
        "linux": "tailwindcss-linux-{arch}",
        "macos": "tailwindcss-macos-{arch}",
    }

    def __init__(self, verbose: bool = True) -> None:
        self.verbose = verbose

    def get_download_url(self, version: str, platform: PlatformInfo) -> str:
        """Generate the download URL for the Tailwind CLI binary."""
        filename = self._get_filename(platform)
        return f"{self.BASE_URL}/download/{version}/{filename}"

    def _get_filename(self, platform: PlatformInfo) -> str:
        """Determine the appropriate filename based on platform."""
        template = self.PLATFORM_FILENAMES.get(platform.os_name)
        if not template:
            raise CommandError(f"Unsupported platform: {platform.os_name}")

        return template.format(arch=platform.architecture)

    def download(self, url: str, destination: Path, show_progress: bool = True) -> None:
        """Download a file from URL to destination with progress tracking."""
        from urllib.error import HTTPError, URLError
        from urllib.request import urlretrieve

        temp_destination = destination.with_suffix(destination.suffix + ".tmp")

        try:
            if self.verbose:
                print(f"\n📥 Downloading from: {url}", Text.INFO)

            def progress_callback(block_num: int, block_size: int, total_size: int) -> None:
                if self.verbose and show_progress and total_size > 0:
                    downloaded = block_num * block_size
                    percent = min(100.0, (downloaded / total_size) * 100)
                    mb_downloaded = downloaded / (1024 * 1024)
                    mb_total = total_size / (1024 * 1024)
                    print(
                        f"\r   Progress: {percent:.1f}% ({mb_downloaded:.2f}/{mb_total:.2f} MB)",
                        end="",
                    )

            urlretrieve(url, temp_destination, progress_callback)

            if self.verbose and show_progress:
                print("")  # New line after progress

            temp_destination.rename(destination)
            if self.verbose:
                print(f"✓ Downloaded to: {destination}", Text.SUCCESS)

        except KeyboardInterrupt:
            self._cleanup_temp_file(temp_destination)
            if self.verbose:
                print("\n⚠ Download cancelled by user.", Text.WARNING)
            raise CommandError("Installation aborted.")
        except HTTPError as e:
            self._cleanup_temp_file(temp_destination)
            raise CommandError(f"Failed to download from {url}. HTTP Error {e.code}: {e.reason}")
        except URLError as e:
            self._cleanup_temp_file(temp_destination)
            raise CommandError(f"Failed to download: {e.reason}")
        except Exception as e:
            self._cleanup_temp_file(temp_destination)
            raise CommandError(f"Download failed: {e}")

    @staticmethod
    def _cleanup_temp_file(temp_file: Path) -> None:
        """Remove temporary file if it exists."""
        if temp_file.exists():
            temp_file.unlink()

    @staticmethod
    def make_executable(file_path: Path) -> None:
        """Make the file executable on Unix-like systems."""
        from platform import system
        from stat import S_IXGRP, S_IXOTH, S_IXUSR

        if system().lower() != "windows":
            current_permissions = file_path.stat().st_mode
            file_path.chmod(current_permissions | S_IXUSR | S_IXGRP | S_IXOTH)


class InstallHandler:
    """Handles the installation of Tailwind CLI."""

    def __init__(self, verbose: bool = True) -> None:
        self.verbose = verbose
        self.downloader = TailwindDownloader(verbose)
        self.validator = TailwindValidator(verbose)

    def install(self, force: bool = False, use_cache: bool = False) -> None:
        """Install the Tailwind CLI binary."""
        platform = PlatformInfo()
        cli_path = TAILWIND.cli
        version = TAILWIND.version

        if self.verbose:
            self._display_platform_info(platform)

        self.validator.ensure_directory(cli_path.parent)
        download_url = self.downloader.get_download_url(version, platform)

        if self.verbose:
            self._display_download_info(version, platform, cli_path, download_url)

        # Check if we should use cached version
        if cli_path.exists() and use_cache:
            if self.verbose:
                print("\n✓ Using cached Tailwind CLI. Skipping download.\n", Text.SUCCESS)
            return

        # Handle existing file
        if cli_path.exists() and not self._confirm_overwrite(cli_path, force):
            return

        # Confirm download
        if not force and not self._confirm_download():
            return

        # Perform installation
        self._perform_installation(download_url, cli_path, version, platform)

    def _display_platform_info(self, platform: PlatformInfo) -> None:
        """Display detected platform information."""
        print(f"\n🖥 Detected platform: {str(platform)}", Text.INFO)

    def _display_download_info(
        self,
        version: str,
        platform: PlatformInfo,
        cli_path: Path,
        download_url: str,
    ) -> None:
        """Display download information to the user."""
        print("\n" + "=" * 60)
        print("DOWNLOAD INFORMATION", Text.INFO)
        print("=" * 60)
        print(f"  Version:     {version}")
        print(f"  Platform:    {platform}")
        print(f"  Destination: {cli_path}")
        print("=" * 60)

    def _confirm_overwrite(self, cli_path: Path, auto_confirm: bool) -> bool:
        """Confirm overwriting existing CLI file."""
        if auto_confirm:
            cli_path.unlink()
            return True

        if self.verbose:
            print(f"\n⚠ Tailwind CLI already exists at: {cli_path}", Text.WARNING)

        overwrite = input("Overwrite? (y/N): ").strip().lower()
        if overwrite == "y":
            cli_path.unlink()
            if self.verbose:
                print("✓ Existing file removed", Text.SUCCESS)
            return True

        if self.verbose:
            print("❌ Installation cancelled.", Text.WARNING)
        return False

    def _confirm_download(self) -> bool:
        """Confirm download with user."""
        confirm = input("\nProceed with download? (y/N): ")
        if confirm.strip().lower() != "y":
            if self.verbose:
                print("❌ Installation cancelled.", Text.WARNING)
            return False
        return True

    def _perform_installation(
        self,
        download_url: str,
        cli_path: Path,
        version: str,
        platform: PlatformInfo,
    ) -> None:
        """Download and install the Tailwind CLI."""
        self.downloader.download(download_url, cli_path)

        if self.verbose:
            print("\n🔧 Setting executable permissions...", Text.INFO)

        self.downloader.make_executable(cli_path)

        if self.verbose:
            print("\n" + "=" * 60)
            print("✓ INSTALLATION COMPLETE", Text.SUCCESS)
            print("=" * 60)
            print(f"  Location: {cli_path}")
            print(f"  Platform: {platform}")
            print(f"  Version:  {version}")
            print("=" * 60 + "\n")


class TailwindExecutor:
    """Base class for executing Tailwind CLI commands."""

    def __init__(self, verbose: bool = True) -> None:
        self.verbose = verbose
        self.validator = TailwindValidator(verbose)

    def _build_base_command(
        self,
        cli_path: Path,
        source_css: Path,
        output_css: Path,
    ) -> list[str]:
        """Build the base Tailwind CLI command."""
        return [
            str(cli_path),
            "-i",
            str(source_css),
            "-o",
            str(output_css),
            "--minify",
        ]

    def _handle_cli_error(self, error: Exception, cli_path: Path) -> None:
        """Handle CLI execution errors."""
        if isinstance(error, FileNotFoundError):
            raise CommandError(
                f"Tailwind CLI not found at '{cli_path}'. Run '{PKG_NAME} tailwind install' first."
            )
        elif isinstance(error, CalledProcessError):
            raise CommandError(f"Tailwind operation failed: {error}")
        else:
            raise CommandError(f"Unexpected error: {error}")


class BuildHandler(TailwindExecutor):
    """Handles building Tailwind output files."""

    def build(self, skip_if_no_source: bool = False) -> bool:
        """Build the Tailwind output css file."""
        cli_path = TAILWIND.cli
        source_css = TAILWIND.source
        output_css = TAILWIND.output

        # Validate source file
        if not self.validator.validate_source_file(source_css, required=not skip_if_no_source):
            return False

        self.validator.ensure_directory(output_css.parent)
        command = self._build_base_command(cli_path, source_css, output_css)

        try:
            if self.verbose:
                print("   Building Tailwind CSS...", Text.INFO)
                run(command, check=True)
                print("   ✓ Build complete!", Text.SUCCESS)
            else:
                run(command, check=True, stdout=DEVNULL, stderr=DEVNULL)
            return True
        except Exception as e:
            self._handle_cli_error(e, cli_path)
            return False


class WatchHandler(TailwindExecutor):
    """Handles watching and rebuilding Tailwind output files on changes."""

    def __init__(self, verbose: bool = True) -> None:
        super().__init__(verbose)
        self._process: Popen[bytes] | None = None

    def watch(self, skip_if_no_source: bool = False, stop_event: Event | None = None) -> bool:
        """Watch source files and rebuild on changes."""
        cli_path = TAILWIND.cli
        source_css = TAILWIND.source
        output_css = TAILWIND.output

        self.validator.validate_cli_exists(cli_path)

        # Validate source file
        if not self.validator.validate_source_file(source_css, required=not skip_if_no_source):
            return False

        self.validator.ensure_directory(output_css.parent)
        command = self._build_watch_command(cli_path, source_css, output_css)

        try:
            self._execute_watch(command, cli_path, stop_event)
            return True
        except Exception as e:
            self._handle_cli_error(e, cli_path)
            return False

    def _build_watch_command(
        self,
        cli_path: Path,
        source_css: Path,
        output_css: Path,
    ) -> list[str]:
        """Build the Tailwind CLI watch command."""
        command = self._build_base_command(cli_path, source_css, output_css)
        command.append("--watch")
        return command

    def _execute_watch(
        self,
        command: list[str],
        cli_path: Path,
        stop_event: Event | None,
    ) -> None:
        """Execute the Tailwind watch command with guaranteed cleanup."""
        try:
            if self.verbose:
                print("   Starting Tailwind watcher process...", Text.INFO)

            self._process = Popen(command, stdout=DEVNULL, stderr=DEVNULL)

            if self.verbose:
                print("   ✓ Watcher started successfully", Text.SUCCESS)

            if stop_event:
                self._monitor_with_stop_event(stop_event)
            else:
                self._process.wait()

        except KeyboardInterrupt:
            if self.verbose:
                print("\n⚠ Tailwind watcher interrupted", Text.WARNING)
            raise
        finally:
            # Always clean up subprocess, regardless of how we exit
            if self.verbose and self._process:
                print("   Stopping Tailwind watcher process...", Text.INFO)
            self._terminate_process()

    def _monitor_with_stop_event(self, stop_event: Event) -> None:
        """Monitor process with stop event, exit when signaled or process ends."""
        while self._process and self._process.poll() is None:
            if stop_event.wait(timeout=0.5):
                # Stop event signaled - break and let finally cleanup
                break
        # Cleanup happens in finally block of _execute_watch

    def _terminate_process(self) -> None:
        """Terminate the Tailwind watch process gracefully with guaranteed cleanup."""
        if not self._process:
            return

        try:
            # Try graceful termination first
            self._process.terminate()
            try:
                self._process.wait(timeout=2.0)
                if self.verbose:
                    print("   ✓ Watcher stopped cleanly", Text.SUCCESS)
            except Exception:
                # If timeout or other issue, force kill
                try:
                    self._process.kill()
                    self._process.wait()
                    if self.verbose:
                        print("   ⚠ Watcher force-stopped", Text.WARNING)
                except Exception:
                    # Process already dead or other error - suppress
                    pass
        except Exception:
            # Process may already be terminated - suppress errors
            pass
        finally:
            # Always clear the process reference
            self._process = None


class CleanHandler:
    """Handles cleaning of Tailwind output CSS file."""

    def __init__(self, verbose: bool = True) -> None:
        self.verbose = verbose

    def clean(self) -> None:
        """Delete the built Tailwind output CSS file."""
        output_css = TAILWIND.output

        if not output_css.exists():
            if self.verbose:
                print("   No output file to clean", Text.INFO)
            return

        try:
            output_css.unlink()
            if self.verbose:
                print(f"✓ Cleaned output file: {output_css}", Text.SUCCESS)
        except PermissionError:
            raise CommandError(
                f"Permission denied: Cannot delete file at {output_css}. "
                "Ensure the file is not in use and the path is writable."
            )
        except Exception as e:
            raise CommandError(f"Failed to delete file: {e}")


class Command(BaseCommand):
    """Django management command for Tailwind CLI operations."""

    help = "Tailwind CLI management: install, build, watch, and clean operations."

    def add_arguments(self, parser: CommandParser) -> None:
        """Add command-line arguments."""
        # Positional command argument
        parser.add_argument(
            "command",
            nargs="?",
            choices=["install", "build", "clean", "watch"],
            help="Command to execute: install, build, clean, or watch",
        )

        # Flag-based commands (backward compatibility)
        group = parser.add_mutually_exclusive_group(required=False)
        group.add_argument(
            "-i",
            "--install",
            action="store_true",
            help="Download and install the Tailwind CLI executable.",
        )
        group.add_argument(
            "-b",
            "--build",
            action="store_true",
            help="Build the Tailwind output CSS file.",
        )
        group.add_argument(
            "-cl",
            "--clean",
            action="store_true",
            help="Delete the built Tailwind output CSS file.",
        )
        group.add_argument(
            "-w",
            "--watch",
            action="store_true",
            help="Watch source files and rebuild on changes.",
        )

        # Additional options
        parser.add_argument(
            "-y",
            "--force",
            action="store_true",
            help="Automatically confirm all prompts.",
        )
        parser.add_argument(
            "--use-cache",
            action="store_true",
            help="Skip download if CLI already exists.",
        )
        parser.add_argument(
            "--no-verbose",
            action="store_true",
            help="Suppress output messages.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Main command handler."""
        command_type = self._determine_command(options)
        self._validate_options(command_type, options)
        verbose = not options.get("no_verbose", False)
        self._execute_command(command_type, options, verbose)

    def _determine_command(self, options: dict[str, Any]) -> str:
        """Determine which command to execute."""
        command = options.get("command")
        commands: dict[str, bool] = {
            "install": command == "install" or options.get("install", False),
            "build": command == "build" or options.get("build", False),
            "clean": command == "clean" or options.get("clean", False),
            "watch": command == "watch" or options.get("watch", False),
        }

        active_commands = [cmd for cmd, active in commands.items() if active]

        if len(active_commands) == 0:
            raise CommandError(
                "You must specify a command: install, build, clean, or watch. "
                "Use 'tailwind --help' for usage information."
            )
        elif len(active_commands) > 1:
            raise CommandError("Only one command can be specified at a time.")

        return active_commands[0]

    def _validate_options(self, command_type: str, options: dict[str, Any]) -> None:
        """Validate command options."""
        if command_type != "install" and options.get("use_cache", False):
            raise CommandError("The --use-cache option can only be used with install.")

    def _execute_command(
        self,
        command_type: str,
        options: dict[str, Any],
        verbose: bool,
    ) -> None:
        """Execute the specified command."""
        handlers: dict[str, Callable[[], Any]] = {
            "install": lambda: InstallHandler(verbose).install(
                force=options.get("force", False),
                use_cache=options.get("use_cache", False),
            ),
            "build": lambda: BuildHandler(verbose).build(),
            "watch": lambda: WatchHandler(verbose).watch(),
            "clean": lambda: CleanHandler(verbose).clean(),
        }

        handlers[command_type]()
