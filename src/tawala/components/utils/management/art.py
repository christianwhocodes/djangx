import shutil

from enum import IntEnum, StrEnum

from django.core.management.base import BaseCommand

from ....conf.post import PKG_NAME


class ArtType(StrEnum):
    """Enumeration of available ASCII art types."""

    PROG_NAME = PKG_NAME
    DEV = "dev"
    BUILD = "build"
    INSTALL = "install"


class TerminalSize(IntEnum):
    """Terminal size threshold for ASCII art.

    Used to determine whether to display the full ASCII banner or a compact version.

    Attributes:
        THRESHOLD: Minimum terminal width (in columns) required for full ASCII art.
    """

    THRESHOLD = 60


class ArtPrinter:
    """Handles printing of ASCII art banners with terminal adaptation.

    Provides consistent formatting and styling for ASCII art across
    different management commands.
    """

    def __init__(self, command: BaseCommand) -> None:
        """Initialize the ASCII art printer.

        Args:
            command: The Django BaseCommand instance for stdout/styling.
        """
        self.command = command
        self.terminal_width = shutil.get_terminal_size(fallback=(80, 24)).columns

    def _get_prog_name_art(self) -> list[str]:
        """Get ASCII art based on terminal width.

        Returns:
            List of strings representing the ASCII art lines.
        """
        if self.terminal_width >= TerminalSize.THRESHOLD:
            return [
                "",
                "  ████████╗ █████╗ ██╗    ██╗ █████╗ ██╗      █████╗ ",
                "  ╚══██╔══╝██╔══██╗██║    ██║██╔══██╗██║     ██╔══██╗",
                "     ██║   ███████║██║ █╗ ██║███████║██║     ███████║",
                "     ██║   ██╔══██║██║███╗██║██╔══██║██║     ██╔══██║",
                "     ██║   ██║  ██║╚███╔███╔╝██║  ██║███████╗██║  ██║",
                "     ╚═╝   ╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝",
                "",
            ]
        else:
            return [
                "",
                "  ▀█▀ ▄▀█ █░█░█ ▄▀█ █░░ ▄▀█",
                "  ░█░ █▀█ ▀▄▀▄▀ █▀█ █▄▄ █▀█",
                "",
            ]

    def _get_dev_art(self) -> list[str]:
        """Get Dev server ASCII art based on terminal width.

        Returns:
            List of strings representing the ASCII art lines.
        """
        prog_name_art = self._get_prog_name_art()

        if self.terminal_width >= TerminalSize.THRESHOLD:
            dev_art = [
                "        ██████╗ ███████╗██╗   ██╗",
                "        ██╔══██╗██╔════╝██║   ██║",
                "        ██║  ██║█████╗  ██║   ██║",
                "        ██║  ██║██╔══╝  ╚██╗ ██╔╝",
                "        ██████╔╝███████╗ ╚████╔╝ ",
                "        ╚═════╝ ╚══════╝  ╚═══╝  ",
                "",
            ]
        else:
            dev_art = [
                "       █▀▄ █▀▀ █░█",
                "       █▄▀ ██▄ ▀▄▀",
                "",
            ]

        return prog_name_art + dev_art

    def _get_build_art(self) -> list[str]:
        """Get Build ASCII art based on terminal width.

        Returns:
            List of strings representing the ASCII art lines.
        """
        prog_name_art = self._get_prog_name_art()

        if self.terminal_width >= TerminalSize.THRESHOLD:
            build_art = [
                "        ██████╗ ██╗   ██╗██╗██╗     ██████╗ ",
                "        ██╔══██╗██║   ██║██║██║     ██╔══██╗",
                "        ██████╔╝██║   ██║██║██║     ██║  ██║",
                "        ██╔══██╗██║   ██║██║██║     ██║  ██║",
                "        ██████╔╝╚██████╔╝██║███████╗██████╔╝",
                "        ╚═════╝  ╚═════╝ ╚═╝╚══════╝╚═════╝ ",
                "",
            ]
        else:
            build_art = [
                "       █▄▄ █░█ █ █░░ █▀▄",
                "       █▄█ █▄█ █ █▄▄ █▄▀",
                "",
            ]

        return prog_name_art + build_art

    def _get_install_art(self) -> list[str]:
        """Get Install ASCII art based on terminal width.

        Returns:
            List of strings representing the ASCII art lines.
        """
        prog_name_art = self._get_prog_name_art()

        if self.terminal_width >= TerminalSize.THRESHOLD:
            install_art = [
                "   ██╗███╗   ██╗███████╗████████╗ █████╗ ██╗     ██╗     ",
                "   ██║████╗  ██║██╔════╝╚══██╔══╝██╔══██╗██║     ██║     ",
                "   ██║██╔██╗ ██║███████╗   ██║   ███████║██║     ██║     ",
                "   ██║██║╚██╗██║╚════██║   ██║   ██╔══██║██║     ██║     ",
                "   ██║██║ ╚████║███████║   ██║   ██║  ██║███████╗███████╗",
                "   ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚══════╝",
                "",
            ]
        else:
            install_art = [
                "    █ █▄░█ █▀ ▀█▀ ▄▀█ █░░ █░░",
                "    █ █░▀█ ▄█ ░█░ █▀█ █▄▄ █▄▄",
                "",
            ]

        return prog_name_art + install_art

    def _get_art(self, art_type: ArtType) -> list[str]:
        """Get ASCII art lines for the specified type.

        Args:
            art_type: The type of ASCII art to retrieve.

        Returns:
            List of strings representing the ASCII art lines.

        Raises:
            ValueError: If an unknown art type is provided.
        """
        art_getters = {
            ArtType.PROG_NAME: self._get_prog_name_art,
            ArtType.DEV: self._get_dev_art,
            ArtType.BUILD: self._get_build_art,
            ArtType.INSTALL: self._get_install_art,
        }

        getter = art_getters.get(art_type)
        if getter is None:
            raise ValueError(f"Unknown art type: {art_type}")

        return getter()

    def _print_banner(
        self,
        art_type: ArtType,
        title: str,
        subtitle: str | None = None,
        notice: str | None = None,
    ) -> None:
        """Print a complete ASCII art banner with optional subtitle and notice.

        Args:
            art_type: The type of ASCII art to display.
            title: Main title text (e.g., "🔥  Development Server  🔥").
            subtitle: Optional subtitle text (e.g., warning messages).
            notice: Optional notice text (e.g., "Press Ctrl-C to quit").
        """
        art_lines = self._get_art(art_type)

        # Print ASCII art
        for line in art_lines:
            self.command.stdout.write(self.command.style.HTTP_INFO(line))

        # Print title
        self.command.stdout.write(self.command.style.HTTP_INFO(title))

        # Print subtitle if provided
        if subtitle:
            self.command.stdout.write(self.command.style.WARNING(subtitle))

        # Print notice if provided
        if notice:
            self.command.stdout.write(self.command.style.NOTICE(notice))

        self.command.stdout.write("")

    def print_dev_banner(self) -> None:
        """Print the development server banner."""
        if self.terminal_width >= TerminalSize.THRESHOLD:
            self._print_banner(
                art_type=ArtType.DEV,
                title="         🔥  Development Server  🔥",
                subtitle="       ⚠️  Not suitable for production!  ⚠️",
                notice="             Press Ctrl-C to quit",
            )
        else:
            self._print_banner(
                art_type=ArtType.DEV,
                title="    🔥  Dev Server  🔥",
                subtitle="  ⚠️   Not for production! ⚠️",
                notice="       Ctrl-C to quit",
            )

    def print_run_process_banner(
        self, art_type: ArtType, display_mode: str, command_count: int
    ) -> None:
        """Print a banner for command processes (build/install).

        Args:
            art_type: The type of ASCII art to display.
            display_mode: The display mode text (e.g., "BUILD", "DRY RUN").
            command_count: Number of commands to execute.
        """
        if self.terminal_width >= TerminalSize.THRESHOLD:
            self._print_banner(
                art_type=art_type,
                title=f"              🔨  {display_mode} Process  🔨",
                notice=f"           {command_count} command(s) to execute",
            )
        else:
            self._print_banner(
                art_type=art_type,
                title=f"      🔨  {display_mode}  🔨",
                notice=f"    {command_count} command(s)",
            )
