"""
Management command for Tailwind CLI installation and build management.

This module provides a clean, OOP-based interface for:
- Installing the Tailwind CLI binary
- Building Tailwind output files
- Watching Tailwind source files for changes
- Cleaning generated CSS files
"""

from pathlib import Path
from platform import system
from stat import S_IXGRP, S_IXOTH, S_IXUSR
from subprocess import DEVNULL, CalledProcessError, run
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlretrieve

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

        Args:
            source_css: Path to the source CSS file.
            required: If True, raise error. If False, return False and optionally warn.

        Returns:
            True if file exists and is valid, False otherwise.
        """
        if not source_css.exists() or not source_css.is_file():
            if required:
                raise CommandError(f"Tailwind source css file not found: {source_css}")
            else:
                if self.verbose:
                    print(
                        f"⚠ Tailwind source file not found: {source_css}. Skipping Tailwind operations.",
                        Text.WARNING,
                    )
                return False
        return True

    def ensure_directory(self, directory: Path) -> None:
        """Ensure a directory exists with proper error handling."""
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise CommandError(
                f"Permission denied: Cannot create directory at {directory}. "
                f"Ensure the path is writable."
            )


class TailwindDownloader:
    """Handles downloading and installation of Tailwind CLI."""

    BASE_URL = "https://github.com/tailwindlabs/tailwindcss/releases"

    def __init__(self, verbose: bool = True) -> None:
        self.verbose = verbose

    def get_download_url(self, version: str, platform: PlatformInfo) -> str:
        """Generate the download URL for the Tailwind CLI binary."""
        filename = self._get_filename(platform)
        return f"{self.BASE_URL}/download/{version}/{filename}"

    def _get_filename(self, platform: PlatformInfo) -> str:
        """Determine the appropriate filename based on platform."""
        if platform.os_name == "windows":
            return "tailwindcss-windows-x64.exe"
        elif platform.os_name == "linux":
            return f"tailwindcss-linux-{platform.architecture}"
        elif platform.os_name == "macos":
            return f"tailwindcss-macos-{platform.architecture}"
        else:
            raise CommandError(f"Unsupported platform: {platform.os_name}")

    def download(self, url: str, destination: Path, show_progress: bool = True) -> None:
        """Download a file from URL to destination with progress tracking."""
        temp_destination = destination.with_suffix(destination.suffix + ".tmp")

        try:
            if self.verbose:
                print(f"Downloading from: {url}")

            def progress_callback(block_num: int, block_size: int, total_size: int) -> None:
                if self.verbose and show_progress and total_size > 0:
                    downloaded = block_num * block_size
                    percent = min(100.0, (downloaded / total_size) * 100)
                    print(f"\rProgress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end="")

            urlretrieve(url, temp_destination, progress_callback)

            if self.verbose and show_progress:
                print("")

            temp_destination.rename(destination)
            if self.verbose:
                print(f"✓ Downloaded to: {destination}")

        except KeyboardInterrupt:
            self._cleanup_temp_file(temp_destination)
            if self.verbose:
                print("\nDownload cancelled by user.")
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
        if self.verbose:
            self._display_platform_info(platform)

        cli_path = TAILWIND.cli
        self.validator.ensure_directory(cli_path.parent)

        version = TAILWIND.version
        download_url = self.downloader.get_download_url(version, platform)

        if self.verbose:
            self._display_download_info(version, platform, cli_path, download_url)

        if self._should_use_cache(cli_path, use_cache):
            return

        if not self._handle_existing_file(cli_path, force):
            return

        if not self._confirm_download(force):
            return

        self._perform_installation(download_url, cli_path, version, platform)

    def _display_platform_info(self, platform: PlatformInfo) -> None:
        """Display detected platform information."""
        print(f"Detected platform: {str(platform)}", Text.SUCCESS)

    def _display_download_info(
        self,
        version: str,
        platform: PlatformInfo,
        cli_path: Path,
        download_url: str,
    ) -> None:
        """Display download information to the user."""
        print("\nDownload Information:")
        print(f"  Version:     {version}")
        print(f"  Platform:    {platform}")
        print(f"  URL:         {download_url}\n")
        print(f"  Destination: {cli_path}")

    def _should_use_cache(self, cli_path: Path, use_cache: bool) -> bool:
        """Check if cached CLI should be used."""
        if cli_path.exists() and use_cache:
            if self.verbose:
                print("\nUsing cached Tailwind CLI. Skipping download.\n", Text.INFO)
            return True
        return False

    def _handle_existing_file(self, cli_path: Path, auto_confirm: bool) -> bool:
        """Handle existing CLI file. Returns True if installation should continue."""
        if not cli_path.exists():
            return True

        if auto_confirm:
            cli_path.unlink()
            return True

        if self.verbose:
            print(f"\n⚠ Tailwind CLI already exists at: {cli_path}", Text.WARNING)
        overwrite = input("Overwrite? (y/N): ").strip().lower()

        if overwrite == "y":
            cli_path.unlink()
            return True

        if self.verbose:
            print("Installation cancelled.")
        return False

    def _confirm_download(self, force: bool) -> bool:
        """Confirm download with user unless auto-confirmed (force)."""
        if force:
            return True

        confirm = input("\nProceed with download? (y/N): ")

        if confirm.strip().lower() != "y":
            if self.verbose:
                print("Installation cancelled.")
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
        self.downloader.make_executable(cli_path)

        if self.verbose:
            print(
                f"\n✓ Tailwind CLI successfully installed at: {cli_path}\n"
                f"  Platform: {platform}\n"
                f"  Version: {version}",
                Text.SUCCESS,
            )


class BuildHandler:
    """Handles building Tailwind output files."""

    def __init__(self, verbose: bool = True) -> None:
        self.verbose = verbose
        self.validator = TailwindValidator(verbose)

    def build(self, skip_if_no_source: bool = False) -> bool:
        """Build the Tailwind output css file.

        Args:
            skip_if_no_source: If True, skip build silently if source doesn't exist.

        Returns:
            True if build succeeded, False if skipped.
        """
        cli_path: Path = TAILWIND.cli
        source_css: Path = TAILWIND.source
        output_css: Path = TAILWIND.output

        # Check source file
        if not self.validator.validate_source_file(source_css, required=not skip_if_no_source):
            return False

        self.validator.ensure_directory(output_css.parent)

        command = self._build_command(cli_path, source_css, output_css)
        self._execute_build(command, cli_path)
        return True

    @staticmethod
    def _build_command(cli_path: Path, source_css: Path, output_css: Path) -> list[str]:
        """Build the Tailwind CLI command."""
        return [
            str(cli_path),
            "-i",
            str(source_css),
            "-o",
            str(output_css),
            "--minify",
        ]

    def _execute_build(self, command: list[str], cli_path: Path) -> None:
        """Execute the Tailwind build command."""
        try:
            if self.verbose:
                print("Building Tailwind output CSS file...")
                run(command, check=True)
                print("✓ Tailwind output CSS file built successfully!", Text.SUCCESS)
            else:
                # Suppress all output from Tailwind CLI
                run(command, check=True, stdout=DEVNULL, stderr=DEVNULL)
        except FileNotFoundError:
            raise CommandError(
                f"Tailwind CLI not found at '{cli_path}'. Run '{PKG_NAME} tailwind install' first."
            )
        except CalledProcessError as e:
            raise CommandError(f"Tailwind build failed: {e}")
        except Exception as e:
            raise CommandError(f"Unexpected error: {e}")


class WatchHandler:
    """Handles watching and rebuilding Tailwind output files on changes."""

    def __init__(self, verbose: bool = True) -> None:
        self.verbose = verbose
        self.validator = TailwindValidator(verbose)

    def watch(self, skip_if_no_source: bool = False) -> bool:
        """Watch source files and rebuild on changes.

        Args:
            skip_if_no_source: If True, skip watch silently if source doesn't exist.

        Returns:
            True if watch started, False if skipped.
        """
        cli_path: Path = TAILWIND.cli
        source_css: Path = TAILWIND.source
        output_css: Path = TAILWIND.output

        self.validator.validate_cli_exists(cli_path)

        # Check source file
        if not self.validator.validate_source_file(source_css, required=not skip_if_no_source):
            return False

        self.validator.ensure_directory(output_css.parent)

        command = self._build_watch_command(cli_path, source_css, output_css)
        self._execute_watch(command, cli_path)
        return True

    @staticmethod
    def _build_watch_command(cli_path: Path, source_css: Path, output_css: Path) -> list[str]:
        """Build the Tailwind CLI watch command."""
        return [
            str(cli_path),
            "-i",
            str(source_css),
            "-o",
            str(output_css),
            "--watch",
            "--minify",
        ]

    def _execute_watch(self, command: list[str], cli_path: Path) -> None:
        """Execute the Tailwind watch command."""
        try:
            if self.verbose:
                print("Watching Tailwind source files for changes...")

            # Run the watch command (this blocks until interrupted)
            run(command, check=True, stdout=DEVNULL, stderr=DEVNULL)

        except KeyboardInterrupt:
            if self.verbose:
                print("\nTailwind watcher stopped.", Text.WARNING)
        except FileNotFoundError:
            raise CommandError(
                f"Tailwind CLI not found at '{cli_path}'. Run '{PKG_NAME} tailwind install' first."
            )
        except CalledProcessError as e:
            raise CommandError(f"Tailwind watch failed: {e}")
        except Exception as e:
            raise CommandError(f"Unexpected error: {e}")


class CleanHandler:
    """Handles cleaning of Tailwind output CSS file."""

    def __init__(self, verbose: bool = True) -> None:
        self.verbose = verbose

    def clean(self) -> None:
        """Delete the built Tailwind output CSS file."""
        output_css: Path = TAILWIND.output

        if not output_css.exists():
            return

        self._delete_output_file(output_css)

    def _delete_output_file(self, output_css: Path) -> None:
        """Delete the output CSS file."""
        try:
            output_css.unlink()
            if self.verbose:
                print(f"✓ Deleted Tailwind output file: {output_css}", Text.SUCCESS)
        except PermissionError:
            raise CommandError(
                f"Permission denied: Cannot delete file at {output_css}. "
                f"Ensure the file is not in use and the path is writable."
            )
        except Exception as e:
            raise CommandError(f"Failed to delete file: {e}")


class Command(BaseCommand):
    """Django management command for Tailwind CLI operations."""

    help = "Tailwind CLI management: install, build, watch, and clean operations."

    def add_arguments(self, parser: CommandParser) -> None:
        """Add command-line arguments."""
        self._add_command_argument(parser)
        self._add_flag_arguments(parser)
        self._add_option_arguments(parser)

    def _add_command_argument(self, parser: CommandParser) -> None:
        """Add the main command positional argument."""
        parser.add_argument(
            "command",
            nargs="?",
            choices=["install", "build", "clean", "watch"],
            help="Command to execute: install, build, clean, or watch",
        )

    def _add_flag_arguments(self, parser: CommandParser) -> None:
        """Add flag-based command options (for backward compatibility)."""
        group = parser.add_mutually_exclusive_group(required=False)
        group.add_argument(
            "-i",
            "--install",
            dest="install",
            action="store_true",
            help="Download and install the Tailwind CLI executable.",
        )
        group.add_argument(
            "-b",
            "--build",
            dest="build",
            action="store_true",
            help="Build the Tailwind output CSS file.",
        )
        group.add_argument(
            "-cl",
            "--clean",
            dest="clean",
            action="store_true",
            help="Delete the built Tailwind output CSS file.",
        )
        group.add_argument(
            "-w",
            "--watch",
            dest="watch",
            action="store_true",
            help="Watch source files and rebuild on changes.",
        )

    def _add_option_arguments(self, parser: CommandParser) -> None:
        """Add additional option arguments."""
        parser.add_argument(
            "-y",
            "--force",
            dest="force",
            action="store_true",
            help="Automatically confirm all prompts.",
        )
        parser.add_argument(
            "--use-cache",
            dest="use_cache",
            action="store_true",
            help="Skip download if CLI already exists.",
        )
        parser.add_argument(
            "--no-verbose",
            dest="no_verbose",
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
        is_install = command == "install" or options.get("install", False)
        is_build = command == "build" or options.get("build", False)
        is_clean = command == "clean" or options.get("clean", False)
        is_watch = command == "watch" or options.get("watch", False)

        command_count = sum([is_install, is_build, is_clean, is_watch])

        if command_count == 0:
            raise CommandError(
                "You must specify a command: install, build, clean, or watch. "
                "Use 'tailwind --help' for usage information."
            )
        elif command_count > 1:
            raise CommandError("Only one command can be specified at a time.")

        if is_install:
            return "install"
        elif is_build:
            return "build"
        elif is_watch:
            return "watch"
        else:
            return "clean"

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
        if command_type == "install":
            handler = InstallHandler(verbose)
            handler.install(
                force=options.get("force", False),
                use_cache=options.get("use_cache", False),
            )
        elif command_type == "build":
            handler = BuildHandler(verbose)
            handler.build()
        elif command_type == "watch":
            handler = WatchHandler(verbose)
            handler.watch()
        elif command_type == "clean":
            handler = CleanHandler(verbose)
            handler.clean()
