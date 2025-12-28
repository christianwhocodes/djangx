from pathlib import Path
from platform import machine, system
from stat import S_IXGRP, S_IXOTH, S_IXUSR
from subprocess import CalledProcessError, run
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import urlretrieve

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser


class Command(BaseCommand):
    help = "TailwindCSS CLI Management commands for installing and building."

    def add_arguments(self, parser: CommandParser) -> None:
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "-b",
            "--build",
            dest="build",
            action="store_true",
            help="Build the TailwindCSS file.",
        )
        group.add_argument(
            "-i",
            "--install",
            dest="install",
            action="store_true",
            help="Download and install the TailwindCSS CLI executable.",
        )

        parser.add_argument(
            "-y",
            "--yes",
            dest="auto_confirm",
            action="store_true",
            help="Automatically confirm all prompts (overwrites existing file unless --use-cache is also set).",
        )

        parser.add_argument(
            "--use-cache",
            dest="use_cache",
            action="store_true",
            help="If CLI already exists, skip prompt and skip downloading without overwriting (even when -y is used).",
        )

    def _get_platform_info(self) -> tuple[str, str]:
        system_platform: str = system().lower()
        machine_platform: str = machine().lower()

        platform_map: dict[str, str] = {
            "darwin": "macos",
            "linux": "linux",
            "windows": "windows",
        }

        platform_name: Optional[str] = platform_map.get(system_platform)
        if not platform_name:
            raise CommandError(
                f"Unsupported operating system: {system_platform}. Supported: Linux, macOS, Windows"
            )

        arch_map: dict[str, str] = {
            "x86_64": "x64",
            "amd64": "x64",
            "x64": "x64",
            "arm64": "arm64",
            "aarch64": "arm64",
            "armv8": "arm64",
        }

        architecture: Optional[str] = arch_map.get(machine_platform)
        if not architecture:
            raise CommandError(
                f"Unsupported architecture: {machine_platform}. Supported: x64, arm64"
            )

        return platform_name, architecture

    def _get_download_url(self, version: str, platform_name: str, architecture: str) -> str:
        base_url: str = "https://github.com/tailwindlabs/tailwindcss/releases"

        if platform_name == "windows":
            filename: str = "tailwindcss-windows-x64.exe"
        elif platform_name == "linux":
            filename = f"tailwindcss-linux-{architecture}"
        elif platform_name == "macos":
            filename = f"tailwindcss-macos-{architecture}"
        else:
            raise CommandError(f"Unsupported platform: {platform_name}")

        return f"{base_url}/download/{version}/{filename}"

    def _download_file(self, url: str, destination: Path, show_progress: bool = True) -> None:
        temp_destination: Path = destination.with_suffix(destination.suffix + ".tmp")

        try:
            self.stdout.write(f"Downloading from: {url}")

            def progress_callback(block_num: int, block_size: int, total_size: int) -> None:
                if show_progress and total_size > 0:
                    downloaded: int = block_num * block_size
                    percent: float = min(100.0, (downloaded / total_size) * 100)
                    self.stdout.write(
                        f"\rProgress: {percent:.1f}% ({downloaded}/{total_size} bytes)",
                        ending="",
                    )
                    self.stdout.flush()

            urlretrieve(url, temp_destination, progress_callback)

            if show_progress:
                self.stdout.write("")

            temp_destination.rename(destination)
            self.stdout.write(self.style.SUCCESS(f"✓ Downloaded to: {destination}"))

        except KeyboardInterrupt:
            if temp_destination.exists():
                temp_destination.unlink()
            self.stdout.write("\n")
            self.stdout.write(self.style.WARNING("Download cancelled by user."))
            raise CommandError("Installation aborted.")
        except HTTPError as e:
            if temp_destination.exists():
                temp_destination.unlink()
            raise CommandError(f"Failed to download from {url}. HTTP Error {e.code}: {e.reason}")
        except URLError as e:
            if temp_destination.exists():
                temp_destination.unlink()
            raise CommandError(f"Failed to download: {e.reason}")
        except Exception as e:
            if temp_destination.exists():
                temp_destination.unlink()
            raise CommandError(f"Download failed: {e}")

    def _make_executable(self, file_path: Path) -> None:
        if system().lower() != "windows":
            current_permissions: int = file_path.stat().st_mode
            file_path.chmod(current_permissions | S_IXUSR | S_IXGRP | S_IXOTH)
            self.stdout.write(self.style.SUCCESS(f"✓ Made executable: {file_path}"))

    def handle_install(
        self,
        tailwindcss_config: dict[str, Any],
        auto_confirm: bool = False,
        use_cache: bool = False,
    ) -> None:
        platform_name, architecture = self._get_platform_info()
        self.stdout.write(
            f"Detected platform: {self.style.SUCCESS(f'{platform_name}-{architecture}')}"
        )

        tailwindcss_cli: Path = tailwindcss_config["CLI"]

        try:
            tailwindcss_cli.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise CommandError(
                f"Permission denied: Cannot create directory at {tailwindcss_cli.parent}. "
                f"Ensure the path is writable."
            )

        tailwindcss_version: str = tailwindcss_config["VERSION"]
        download_url: str = self._get_download_url(tailwindcss_version, platform_name, architecture)

        self.stdout.write("\nDownload Information:")
        self.stdout.write(f"  Version:     {tailwindcss_version}")
        self.stdout.write(f"  Platform:    {platform_name}-{architecture}")
        self.stdout.write(f"  Destination: {tailwindcss_cli}")
        self.stdout.write(f"  URL:         {download_url}\n")

        # ---- CACHE LOGIC BRANCH ----
        if tailwindcss_cli.exists() and use_cache:
            self.stdout.write(
                self.style.HTTP_NOT_MODIFIED("\nUsing cached TailwindCSS CLI. Skipping download.\n")
            )
            return  # continue silently without overwriting

        # ---- EXIST LOGIC BRANCH ----
        if tailwindcss_cli.exists():
            if auto_confirm:
                # auto-confirm alone overwrites, but NOT when cache is set - handled above
                tailwindcss_cli.unlink()
            else:
                self.stdout.write(
                    self.style.WARNING(f"\n⚠ TailwindCSS CLI already exists at: {tailwindcss_cli}")
                )
                overwrite: str = input("Overwrite? (y/N): ").strip().lower()
                if overwrite != "y":
                    self.stdout.write("Installation cancelled.")
                    return
                else:
                    tailwindcss_cli.unlink()
        else:
            # Confirm download if not auto-confirmed
            if not auto_confirm:
                confirm: str = input("\nProceed with download? (y/N): ").strip().lower()
                if confirm != "y":
                    self.stdout.write("Installation cancelled.")
                    return

        # Download and install
        self._download_file(download_url, tailwindcss_cli)
        self._make_executable(tailwindcss_cli)

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ TailwindCSS CLI successfully installed at: {tailwindcss_cli}\n"
                f"  Platform: {platform_name}-{architecture}\n"
                f"  Version: {tailwindcss_version}"
            )
        )

    def handle_build(self, tailwindcss_config: dict[str, Any]) -> None:
        tailwindcss_cli: Path = tailwindcss_config["CLI"]
        source_css: Path = tailwindcss_config["SOURCE"]
        output_css: Path = tailwindcss_config["OUTPUT"]

        if not source_css.exists() or not source_css.is_file():
            raise CommandError(f"TailwindCSS source file not found or invalid: {source_css}")

        command: list[str] = [
            str(tailwindcss_cli),
            "-i",
            str(source_css),
            "-o",
            str(output_css),
            "--minify",
        ]

        try:
            self.stdout.write("Building TailwindCSS output file...")
            run(command, check=True)
            self.stdout.write(self.style.SUCCESS("✓ TailwindCSS output file built successfully!"))
        except FileNotFoundError:
            raise CommandError(
                f"TailwindCSS CLI not found at '{tailwindcss_cli}'. Run {settings.PKG_NAME} tailwindcss --install first."
            )
        except CalledProcessError as e:
            raise CommandError(f"TailwindCSS build failed: {e}")
        except Exception as e:
            raise CommandError(f"Unexpected error: {e}")

    def handle(self, *args: Any, **options: Any) -> None:
        tailwindcss_config = settings.TAILWINDCSS
        # Validate that use_cache is not used with build
        if options["build"] and options.get("use_cache", False):
            raise CommandError(
                "The --use-cache option can only be used with [-i, --install], not with [-b, --build]."
            )

        if options["install"]:
            self.handle_install(
                tailwindcss_config,
                auto_confirm=options.get("auto_confirm", False),
                use_cache=options.get("use_cache", False),
            )
        elif options["build"]:
            self.handle_build(tailwindcss_config)
