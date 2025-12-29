from pathlib import Path
from subprocess import DEVNULL, Popen
from threading import Lock, Thread
from typing import ClassVar, Optional

from christianwhocodes.stdout import Text, print
from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.safestring import SafeString, mark_safe

register = template.Library()


class TailwindWatcher:
    """Manages the Tailwind CSS watcher process.

    Singleton class that ensures only one watcher process runs at a time.
    The watcher automatically rebuilds CSS when template files change.
    """

    _instance: ClassVar["Optional[TailwindWatcher]"] = None
    _lock: ClassVar[Lock] = Lock()
    _disabled: ClassVar[bool] = False

    def __init__(self) -> None:
        """Initialize the watcher (use get_instance() instead)."""
        self._started: bool = False
        self._thread: Optional[Thread] = None
        self._process: Optional[Popen[bytes]] = None

    @classmethod
    def get_instance(cls) -> "TailwindWatcher":
        """Get or create the singleton watcher instance.

        Returns:
            The singleton TailwindWatcher instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def disable(cls) -> None:
        """Disable the watcher globally."""
        cls._disabled = True

    @classmethod
    def is_disabled(cls) -> bool:
        """Check if the watcher is disabled.

        Returns:
            True if the watcher is disabled, False otherwise
        """
        return cls._disabled

    def start(self, source_css: Path, output_css: Path, cli_path: Path) -> None:
        """Start the watcher if not already running.

        Args:
            source_css: Path to the source CSS file
            output_css: Path to the output CSS file
            cli_path: Path to the Tailwind CLI executable
        """
        if self._disabled:
            return

        with self._lock:
            if self._started:
                return
            self._started = True

        self._thread = Thread(
            target=self._run_watcher,
            args=(source_css, output_css, cli_path),
            daemon=True,
            name="TailwindWatcher",
        )
        self._thread.start()

    def _run_watcher(self, source_css: Path, output_css: Path, cli_path: Path) -> None:
        """Run the watcher process in a background thread.

        Args:
            source_css: Path to the source CSS file
            output_css: Path to the output CSS file
            cli_path: Path to the Tailwind CLI executable
        """
        try:
            self._validate_cli(cli_path)
            self._validate_source(source_css)
            self._ensure_output_directory(output_css)
            self._start_process(source_css, output_css, cli_path)
        except Exception as e:
            print(f"Failed to start Tailwind watcher: {e}", Text.WARNING)

    def _validate_cli(self, cli_path: Path) -> None:
        """Verify the CLI executable exists.

        Args:
            cli_path: Path to the Tailwind CLI executable

        Raises:
            FileNotFoundError: If the CLI doesn't exist
        """
        if not cli_path.exists():
            raise FileNotFoundError(f"Tailwind CLI not found at: {cli_path}")

    def _validate_source(self, source_css: Path) -> None:
        """Verify the source CSS file exists and is a file.

        Args:
            source_css: Path to the source CSS file

        Raises:
            FileNotFoundError: If the source file doesn't exist
            ValueError: If the path exists but is not a file
        """
        if not (source_css.exists() and source_css.is_file()):
            raise FileNotFoundError(f"TailwindCSS source file not found: {source_css}")

    def _ensure_output_directory(self, output_css: Path) -> None:
        """Create the output directory if it doesn't exist.

        Args:
            output_css: Path to the output CSS file

        Raises:
            PermissionError: If directory creation fails
        """
        try:
            output_css.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise PermissionError(
                f"Permission denied: Cannot create directory at {output_css.parent}"
            ) from e

    def _start_process(self, source_css: Path, output_css: Path, cli_path: Path) -> None:
        """Start the Tailwind CLI watch process.

        Args:
            source_css: Path to the source CSS file
            output_css: Path to the output CSS file
            cli_path: Path to the Tailwind CLI executable
        """
        self._process = Popen(
            [str(cli_path), "-i", str(source_css), "-o", str(output_css), "--watch", "--minify"],
            stdout=DEVNULL,
            stderr=DEVNULL,
            start_new_session=True,
        )

    @property
    def is_running(self) -> bool:
        """Check if the watcher is currently running.

        Returns:
            True if the watcher process is running, False otherwise
        """
        return self._started and (self._process is None or self._process.poll() is None)


@register.simple_tag
def tailwindcss() -> SafeString:
    """Generate the CSS link tag and start the Tailwind watcher (in DEBUG mode).

    Returns:
        SafeString containing the CSS link tag HTML
    """
    try:
        config: dict[str, Path] = settings.TAILWINDCSS
        output_css: Path = config["OUTPUT"]

        # Start watcher on first template tag use (only in DEBUG mode and if not disabled)
        if settings.DEBUG and not TailwindWatcher.is_disabled():
            watcher: TailwindWatcher = TailwindWatcher.get_instance()
            watcher.start(source_css=config["SOURCE"], output_css=output_css, cli_path=config["CLI"])

        # Generate the static URL
        output_static_dir: Path = output_css.parent
        while output_static_dir.name != "static" and output_static_dir != output_static_dir.parent:
            output_static_dir = output_static_dir.parent

        relative_path: Path = output_css.relative_to(output_static_dir)
        static_url: str = static(str(relative_path))

        return mark_safe(f"<link rel='stylesheet' href='{static_url}' />")

    except (AttributeError, KeyError) as e:
        print(f"Tailwind configuration error: {e}", Text.WARNING)
        return mark_safe("<!-- Tailwind CSS configuration error -->")
