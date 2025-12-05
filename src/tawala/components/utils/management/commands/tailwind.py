from pathlib import Path
from platform import machine, system
from stat import S_IXGRP, S_IXOTH, S_IXUSR
from subprocess import CalledProcessError, run
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import urlretrieve

from django.core.management.base import BaseCommand, CommandError, CommandParser

from .....core.app.postsettings import CLI_DIR, PKG_NAME, TAILWIND_CLI


class Command(BaseCommand):
    help = "Build Tailwind CSS using the Tailwind CLI."

    def add_arguments(self, parser: CommandParser) -> None:
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "-b",
            "--build",
            dest="build",
            action="store_true",
            help="Build the Tailwind CSS file.",
        )
        group.add_argument(
            "-i",
            "--install",
            dest="install",
            action="store_true",
            help="Download and install the Tailwind CSS CLI executable.",
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
            help="If Tailwind CLI already exists in CLI_DIR, skip prompt and skip downloading without overwriting (even when -y is used).",
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

    def _get_download_url(
        self, version: str, platform_name: str, architecture: str
    ) -> str:
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

    def _download_file(
        self, url: str, destination: Path, show_progress: bool = True
    ) -> None:
        temp_destination: Path = destination.with_suffix(destination.suffix + ".tmp")

        try:
            self.stdout.write(f"Downloading from: {url}")

            def progress_callback(
                block_num: int, block_size: int, total_size: int
            ) -> None:
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
            raise CommandError(
                f"Failed to download from {url}. HTTP Error {e.code}: {e.reason}"
            )
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
        tailwind_config: dict[str, Any],
        auto_confirm: bool = False,
        use_cache: bool = False,
    ) -> None:
        platform_name, architecture = self._get_platform_info()
        self.stdout.write(
            f"Detected platform: {self.style.SUCCESS(f'{platform_name}-{architecture}')}"
        )

        folder: Path = CLI_DIR
        folder.mkdir(parents=True, exist_ok=True)
        tailwind_cli_path = folder / "tailwindcss" / "cli"
        tailwind_cli_version: str = tailwind_config["VERSION"]
        download_url: str = self._get_download_url(
            tailwind_cli_version, platform_name, architecture
        )

        self.stdout.write("\nDownload Information:")
        self.stdout.write(f"  Version:     {tailwind_cli_version}")
        self.stdout.write(f"  Platform:    {platform_name}-{architecture}")
        self.stdout.write(f"  Destination: {tailwind_cli_path}")
        self.stdout.write(f"  URL:         {download_url}\n")

        # ---- CACHE LOGIC BRANCH ----
        if tailwind_cli_path.exists() and use_cache:
            self.stdout.write(
                self.style.HTTP_NOT_MODIFIED(
                    "\nUsing cached Tailwind CLI. Skipping download.\n"
                )
            )
            return  # continue silently without overwriting

        # ---- EXIST LOGIC BRANCH ----
        if tailwind_cli_path.exists():
            if auto_confirm:
                # auto-confirm alone overwrites, but NOT when cache is set - handled above
                tailwind_cli_path.unlink()
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n⚠ Tailwind CLI already exists at: {tailwind_cli_path}"
                    )
                )
                overwrite: str = input("Overwrite? (y/N): ").strip().lower()
                if overwrite != "y":
                    self.stdout.write("Installation cancelled.")
                    return
                else:
                    tailwind_cli_path.unlink()
        else:
            # Confirm download if not auto-confirmed
            if not auto_confirm:
                confirm: str = input("\nProceed with download? (y/N): ").strip().lower()
                if confirm != "y":
                    self.stdout.write("Installation cancelled.")
                    return

        # Download and install
        self._download_file(download_url, tailwind_cli_path)
        self._make_executable(tailwind_cli_path)

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Tailwind CLI successfully installed at: {tailwind_cli_path}\n"
                f"  Platform: {platform_name}-{architecture}\n"
                f"  Version: {tailwind_cli_version}"
            )
        )

    def handle_build(self, tailwind_config: dict[str, Any]) -> None:
        tailwind_cli: Path | str = tailwind_config.get("PATH", "")
        css_config: dict[str, Path | str] = tailwind_config.get("CSS", {})
        input_css = css_config.get("input", "")
        output_css = css_config.get("output", "")

        if not tailwind_cli or not input_css or not output_css:
            raise CommandError(
                "Tailwind CLI configuration is incomplete. Confirm your TAILWIND_CLI configuration."
            )

        command: list[str] = [
            str(tailwind_cli),
            "-i",
            str(input_css),
            "-o",
            str(output_css),
            "--minify",
        ]

        try:
            self.stdout.write("Building Tailwind CSS...")
            run(command, check=True)
            self.stdout.write(self.style.SUCCESS("✓ Tailwind CSS built successfully!"))
        except FileNotFoundError:
            raise CommandError(
                f"Tailwind CLI not found at '{tailwind_cli}'. Run {PKG_NAME} tailwind --install first."
            )
        except CalledProcessError as e:
            raise CommandError(f"Tailwind CSS build failed: {e}")
        except Exception as e:
            raise CommandError(f"Unexpected error: {e}")

    def handle(self, *args: Any, **options: Any) -> None:
        tailwind_config = TAILWIND_CLI
        # Validate that use_cache is not used with build
        if options["build"] and options.get("use_cache", False):
            raise CommandError(
                "The --use-cache option can only be used with [-i, --install], not with [-b, --build]."
            )

        if options["install"]:
            self.handle_install(
                tailwind_config,
                auto_confirm=options.get("auto_confirm", False),
                use_cache=options.get("use_cache", False),
            )
        elif options["build"]:
            self.handle_build(tailwind_config)
