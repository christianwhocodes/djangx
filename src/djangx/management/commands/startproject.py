from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

from christianwhocodes.core import ExitCode, Version
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt

from ... import PKG_DISPLAY_NAME, PKG_NAME, PROJECT_DIR, PROJECT_INIT_NAME

__all__ = ["initialize"]

# ============================================================================
# Configuration & Templates
# ============================================================================

# VCS and common items that shouldn't prevent initialization
SAFE_DIRECTORY_ITEMS: Final[set[str]] = {
    ".git",
    ".gitignore",
    ".gitattributes",
    ".hg",
    ".hgignore",
    "LICENSE",
    "LICENSE.txt",
    "LICENSE.md",
}


class PresetType(StrEnum):
    """Available project presets."""

    DEFAULT = "default"
    VERCEL = "vercel"


@dataclass(frozen=True)
class _ProjectDependencies:
    """Manages project dependencies."""

    base: tuple[str, ...] = (
        "pillow>=12.1.0",
        "psycopg[binary,pool]>=3.3.2",
    )
    dev: tuple[str, ...] = ("djlint>=1.36.4", "ruff>=0.15.0")
    vercel: tuple[str, ...] = ("vercel>=0.3.8",)

    def get_for_preset(self, preset: PresetType) -> list[str]:
        """Get dependencies for a specific preset.

        Args:
            preset: The preset type.

        Returns:
            List of dependency strings including base dependencies.
        """
        deps = list(self.base)
        deps.append(f"{PKG_NAME}>={Version.get(PKG_NAME)[0]}")

        if preset == PresetType.VERCEL:
            deps.extend(self.vercel)

        return deps


class _TemplateManager:
    """Manages all template content for project initialization."""

    @staticmethod
    def gitignore() -> str:
        """Generate .gitignore content."""
        return """
# Python-generated files
__pycache__/
*.py[oc]
build/
dist/
wheels/
*.egg-info

# Virtual environments
/.venv/

# Ruff cache
/.ruff_cache/

# Temporary files
/.tmp/

# Static and media files
/public/

# Environment variables files
/.env*

# SQLite database file
/db.sqlite3
""".strip()

    @staticmethod
    def readme() -> str:
        """Generate README.md content."""
        return f"""
# {PROJECT_INIT_NAME}

A new project built with {PKG_DISPLAY_NAME}.

## Getting Started

1. Install dependencies: `uv sync`
2. Run development server: `djx runserver`
""".strip()

    @staticmethod
    def pyproject_toml(preset: PresetType, dependencies: list[str]) -> str:
        """Generate pyproject.toml content.

        Args:
            preset: The preset type.
            dependencies: List of project dependencies.

        Returns:
            Formatted pyproject.toml content.
        """
        deps = _ProjectDependencies()
        deps_formatted = ",\n    ".join(f'"{dep}"' for dep in dependencies)
        dev_deps_formatted = ",\n    ".join(f'"{dep}"' for dep in deps.dev)

        # Preset-specific tool configuration
        tool_config = ""
        match preset:
            case PresetType.VERCEL:
                tool_config = (
                    '\nstorage = { backend = "vercel", blob-token = "your-vercel-blob-token" }\n'
                )
            case _:
                pass

        return f"""[project]
name = "{PROJECT_INIT_NAME}"
version = "0.1.0"
description = ""
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    {deps_formatted},
]

[dependency-groups]
dev = [
    {dev_deps_formatted},
]

[tool.djlint]
blank_line_before_tag = "block"
blank_line_after_tag = "load,extends,endblock"

[tool.{PKG_NAME}]{tool_config}
"""

    @staticmethod
    def home_urls() -> str:
        """Generate home app urls.py content."""
        return """from django.contrib import admin
from django.urls import URLPattern, URLResolver, path

from . import views

urlpatterns: list[URLPattern | URLResolver] = [
    path("admin/", admin.site.urls),
    path("", views.HomeView.as_view(), name="home"),
]
"""

    @staticmethod
    def home_views() -> str:
        """Generate home app views.py content."""
        return """from django.views.generic.base import TemplateView


class HomeView(TemplateView):
    template_name = "home/index.html"
"""

    @staticmethod
    def home_index_html() -> str:
        """Generate home app index.html content."""
        return """{% extends "ui/index.html" %}

{% load org %}

{% block title %}
  <title>Welcome - {% org "name" %} App</title>
{% endblock title %}

{% block fonts %}
  <link href="https://fonts.googleapis.com" rel="preconnect" />
  <link href="https://fonts.gstatic.com" rel="preconnect" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100;0,300;0,400;0,500;0,700;0,900;1,100;1,300;1,400;1,500;1,700;1,900&family=Raleway:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&family=Mulish:ital,wght@0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap"
        rel="stylesheet" />
{% endblock fonts %}

{% block main %}
  <main>
    <section class="container-full py-8">
    </section>
  </main>
{% endblock main %}
"""

    @staticmethod
    def tailwind_css() -> str:
        """Generate Tailwind CSS content."""
        return f"""@import "tailwindcss";

/* =============================================================================
   SOURCE FILES
   ============================================================================= */
@source "../../../../.venv/**/{PKG_NAME}/ui/templates/ui/**/*.html";
@source "../../../templates/home/**/*.html";

/* =============================================================================
   THEME CONFIGURATION
   ============================================================================= */
@theme {{
  /* ---------------------------------------------------------------------------
     TYPOGRAPHY
     --------------------------------------------------------------------------- */
  /* Default body text font */
  --font-default:
    "Roboto", system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue",
    Arial, "Noto Sans", "Liberation Sans", sans-serif, "Apple Color Emoji",
    "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
  /* Headings font family */
  --font-heading: "Mulish", system-ui, -apple-system, sans-serif;
  /* Navigation font family */
  --font-nav: "Raleway", system-ui, -apple-system, sans-serif;

  /* ---------------------------------------------------------------------------
     COLOR PALETTE - Base color system
     --------------------------------------------------------------------------- */
  /* Accent Colors */
  --color-accent: #ff4d4f; /* Primary accent for your brand (links, CTAs) */
  /* Background Colors */
  --color-background: #141414; /* Main page background */
  --color-surface: #1c1c1c; /* Elevated surfaces (cards, panels) */
  /* Text Colors */
  --color-default: #d9d9d9; /* Default body text */
  --color-heading: #ededed; /* Headings and titles */
  --color-contrast: #ffffff; /* Contrast text elements, ensuring readability against backgrounds, accent, headings, default colors  */

  /* ---------------------------------------------------------------------------
     NAVIGATION COLORS - Navigation component tokens
     --------------------------------------------------------------------------- */
  /* Desktop Navigation */
  --color-nav: #d9d9d9; /* Default nav link color */
  --color-nav-hover: #ff4d4f; /* Nav link hover state */
  /* Mobile Navigation */
  --color-nav-mobile-bg: #2e2e2e; /* Mobile menu background */
  /* Dropdown Menus */
  --color-nav-dropdown-bg: #2e2e2e; /* Dropdown background */
  --color-nav-dropdown: #d9d9d9; /* Dropdown text color */
  --color-nav-dropdown-hover: #ff4d4f; /* Dropdown hover state */
}}

/* =============================================================================
   LIGHT THEME OVERRIDES
   ============================================================================= */
@theme light {{
  --color-background: rgba(41, 41, 41, 0.8);
  --color-surface: #484848;
}}

/* =============================================================================
   DARK THEME OVERRIDES
   ============================================================================= */
@theme dark {{
  --color-background: #060606;
  --color-surface: #252525;
  --color-default: #ffffff;
  --color-heading: #ffffff;
}}

/* =============================================================================
   UTILITY CLASSES
   ============================================================================= */
@layer utilities {{
  /* Full-width container */
  .container-full {{
    @apply mx-auto w-full px-8;
  }}

  /* Responsive container (Mobile→SM→MD→LG→XL→2XL: 100%→92%→83%→80%→75%→1400px max) */
  .container {{
    @apply mx-auto w-full px-8 sm:w-11/12 sm:px-4 md:w-5/6 lg:w-4/5 xl:w-3/4 xl:px-0 2xl:max-w-[1400px];
  }}
}}

/* =============================================================================
   BASE STYLES - Global element styling
   ============================================================================= */
@layer base {{
  :root {{
    @apply scroll-smooth;
  }}

  body {{
    @apply bg-background text-default font-default antialiased;
  }}

  h1,
  h2,
  h3,
  h4,
  h5,
  h6 {{
    @apply text-heading font-heading text-balance;
  }}

  a {{
    @apply text-accent no-underline transition-colors duration-200 ease-in-out;
  }}

  a:hover {{
    color: color-mix(in srgb, var(--color-accent), white 15%);
  }}
}}
"""


# ============================================================================
# File Management
# ============================================================================


class _FileTracker:
    """Tracks files and directories created during initialization for rollback."""

    def __init__(self):
        """Initialize the file tracker."""
        self._created_paths: list[Path] = []

    def track(self, path: Path) -> None:
        """Track a created file or directory.

        Args:
            path: The path that was created.
        """
        if path not in self._created_paths:
            self._created_paths.append(path)

    def cleanup_all(self) -> None:
        """Remove all tracked files and directories in reverse order of creation."""
        from shutil import rmtree

        # Reverse order to remove files before their parent directories
        for path in reversed(self._created_paths):
            try:
                if path.exists():
                    if path.is_dir():
                        rmtree(path)
                    else:
                        path.unlink()
            except Exception:
                # Best effort cleanup - don't raise on cleanup failures
                pass

        self._created_paths.clear()


class _ProjectFileWriter:
    """Handles file writing operations for project initialization."""

    def __init__(self, project_dir: Path, console: Console, tracker: _FileTracker):
        """Initialize the file writer.

        Args:
            project_dir: The project directory path.
            console: Rich console for output.
            tracker: File tracker for rollback support.
        """
        self.project_dir = project_dir
        self.console = console
        self.tracker = tracker

    def write_if_not_exists(self, filename: str, content: str) -> bool:
        """Write content to a file only if it doesn't exist.

        Args:
            filename: Name of the file to create.
            content: Content to write.

        Returns:
            True if file was created, False if it already existed.

        Raises:
            IOError: If file cannot be written.
            PermissionError: If lacking permission to write.
        """
        file_path = self.project_dir / filename

        if file_path.exists():
            return False

        file_path.write_text(content.strip(), encoding="utf-8")
        self.tracker.track(file_path)
        return True

    def write_to_path_if_not_exists(self, path: Path, content: str) -> bool:
        """Write content to a specific path only if it doesn't exist.

        Args:
            path: Full path to the file.
            content: Content to write.

        Returns:
            True if file was created, False if it already existed.

        Raises:
            IOError: If file cannot be written.
            PermissionError: If lacking permission to write.
        """
        if path.exists():
            return False

        path.write_text(content.strip(), encoding="utf-8")
        self.tracker.track(path)
        return True

    def ensure_dir(self, path: Path) -> bool:
        """Ensure a directory exists.

        Args:
            path: Directory path to create.

        Returns:
            True if directory was created, False if it already existed.
        """
        if path.exists():
            return False

        path.mkdir(parents=True, exist_ok=True)
        self.tracker.track(path)
        return True


# ============================================================================
# Home App Creator
# ============================================================================


class _HomeAppCreator:
    """Creates the default 'home' Django application."""

    def __init__(
        self,
        project_dir: Path,
        writer: _ProjectFileWriter,
        templates: _TemplateManager,
        console: Console,
    ):
        """Initialize the home app creator.

        Args:
            project_dir: The project directory path.
            writer: File writer instance.
            templates: Template manager instance.
            console: Rich console for output.
        """
        self.project_dir = project_dir
        self.writer = writer
        self.templates = templates
        self.console = console
        self.home_dir = project_dir / "home"

    def create(self) -> None:
        """Create the home app with all necessary files and directories."""
        # Check if home app already exists
        if self.home_dir.exists():
            self.console.print(
                "[yellow]Home app directory already exists, skipping app creation[/yellow]"
            )
            return

        # Create the Django app structure
        self._create_app_structure()

        # Create app files
        self._create_urls()
        self._create_views()
        self._create_templates()
        self._create_static_files()

    def _create_app_structure(self) -> None:
        """Create the basic Django app structure using startapp command."""
        from django.core.management import call_command

        try:
            call_command("startapp", "home")
            # Track the created directory
            self.writer.tracker.track(self.home_dir)
        except Exception as e:
            raise IOError(f"Failed to create home app: {e}") from e

    def _create_urls(self) -> None:
        """Create urls.py for the home app."""
        urls_path = self.home_dir / "urls.py"
        if self.writer.write_to_path_if_not_exists(urls_path, self.templates.home_urls()):
            pass  # File was created
        else:
            self.console.print("[dim]urls.py already exists, skipping[/dim]")

    def _create_views(self) -> None:
        """Create views.py for the home app."""
        views_path = self.home_dir / "views.py"
        # Only overwrite if it's the default Django startapp content
        if views_path.exists():
            content = views_path.read_text(encoding="utf-8")
            # Check if it's the default Django views.py (contains only imports or is minimal)
            if len(content.strip()) < 100:  # Default Django file is very short
                views_path.write_text(self.templates.home_views().strip(), encoding="utf-8")
        else:
            self.writer.write_to_path_if_not_exists(views_path, self.templates.home_views())

    def _create_templates(self) -> None:
        """Create template directory structure and files."""
        templates_dir = self.home_dir / "templates" / "home"
        self.writer.ensure_dir(templates_dir)

        index_path = templates_dir / "index.html"
        self.writer.write_to_path_if_not_exists(index_path, self.templates.home_index_html())

    def _create_static_files(self) -> None:
        """Create static directory structure and CSS files."""
        static_dir = self.home_dir / "static" / "home" / "css"
        self.writer.ensure_dir(static_dir)

        css_path = static_dir / "tailwind.css"
        self.writer.write_to_path_if_not_exists(css_path, self.templates.tailwind_css())


# ============================================================================
# Main Initializer
# ============================================================================


class ProjectInitializationError(Exception):
    """Raised when project initialization fails."""

    pass


class _ProjectInitializer:
    """Handles the initialization of a new project with proper structure and configuration."""

    def __init__(
        self,
        project_dir: Path,
        dependencies: _ProjectDependencies | None = None,
        templates: _TemplateManager | None = None,
        console: Console | None = None,
    ):
        """Initialize the project initializer.

        Args:
            project_dir: The directory where the project will be created.
            dependencies: Dependency manager (uses default if None).
            templates: Template manager (uses default if None).
            console: Rich console for output (creates new if None).
        """
        self.project_dir = Path(project_dir)
        self.dependencies = dependencies or _ProjectDependencies()
        self.templates = templates or _TemplateManager()
        self.console = console or Console()
        self.tracker = _FileTracker()
        self.writer = _ProjectFileWriter(self.project_dir, self.console, self.tracker)

    def _validate_directory(self, force: bool = False) -> None:
        """Validate that the directory is suitable for initialization.

        Args:
            force: Skip validation and proceed regardless.

        Raises:
            ProjectInitializationError: If directory contains non-VCS files and user declines.
        """
        if force:
            return

        existing_items = list(self.project_dir.iterdir())
        if not existing_items:
            return

        # Filter out safe items
        problematic_items = [
            item for item in existing_items if item.name not in SAFE_DIRECTORY_ITEMS
        ]

        if not problematic_items:
            # Only safe items present - proceed without prompting
            return

        # Show what exists and ask for confirmation
        items_list = "\n  - ".join(item.name for item in problematic_items)

        self.console.print(f"[yellow]Directory is not empty. Found:[/yellow]\n  - {items_list}\n")

        should_proceed = Confirm.ask(
            f"Initialize {PKG_DISPLAY_NAME} project anyway? "
            "This will skip existing files and create new ones",
            default=False,
            console=self.console,
        )

        if not should_proceed:
            raise ProjectInitializationError("Initialization cancelled by user.")

    def _get_preset_choice(self, preset: str | None = None) -> PresetType:
        """Get the user's preset choice or validate the provided one.

        Args:
            preset: Optional preset to use without prompting.

        Returns:
            The chosen preset type.

        Raises:
            ValueError: If preset is invalid.
        """
        if preset:
            try:
                return PresetType(preset)
            except ValueError:
                valid_presets = [p.value for p in PresetType]
                raise ValueError(
                    f"Invalid preset '{preset}'. Must be one of: {', '.join(valid_presets)}"
                ) from None

        choice = Prompt.ask(
            "Choose a preset",
            choices=[p.value for p in PresetType],
            default=PresetType.DEFAULT.value,
            console=self.console,
        )
        return PresetType(choice)

    def _create_core_files(self, preset: PresetType) -> None:
        """Create core project configuration files.

        Args:
            preset: The preset type to use.

        Raises:
            IOError: If files cannot be created.
        """
        dependencies = self.dependencies.get_for_preset(preset)

        # Create files only if they don't exist
        files_to_create = {
            "pyproject.toml": self.templates.pyproject_toml(preset, dependencies),
            ".gitignore": self.templates.gitignore(),
            "README.md": self.templates.readme(),
        }

        for filename, content in files_to_create.items():
            if self.writer.write_if_not_exists(filename, content):
                pass  # File was created
            else:
                self.console.print(f"[dim]{filename} already exists, skipping[/dim]")

    def _configure_preset_files_and_env_example(self, preset: PresetType) -> None:
        """Configure files based on the chosen preset.

        Args:
            preset: The preset configuration to apply.

        Raises:
            IOError: If preset-specific file generation fails.
        """
        from subprocess import CalledProcessError, run

        try:
            match preset:
                case PresetType.VERCEL:
                    # Only generate vercel.json if it doesn't exist
                    if not (self.project_dir / "vercel.json").exists():
                        run(
                            [PKG_NAME, "generate", "-f", "vercel", "-y"],
                            cwd=self.project_dir,
                            check=True,
                            capture_output=True,
                        )
                        # Track the created file
                        self.tracker.track(self.project_dir / "vercel.json")
                    else:
                        self.console.print("[dim]vercel.json already exists, skipping[/dim]")

                    # Only generate api/server.py if it doesn't exist
                    server_path = self.project_dir / "api" / "server.py"
                    if not server_path.exists():
                        run(
                            [PKG_NAME, "generate", "-f", "server", "-y"],
                            cwd=self.project_dir,
                            check=True,
                            capture_output=True,
                        )
                        # Track the created files
                        self.tracker.track(self.project_dir / "api")
                    else:
                        self.console.print("[dim]api/server.py already exists, skipping[/dim]")
                case _:
                    # Future presets will be added here
                    pass

        except CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            raise IOError(f"Failed to generate preset-specific files: {error_msg}") from e
        except FileNotFoundError as e:
            raise IOError(
                f"Command '{PKG_NAME}' not found. Ensure {PKG_DISPLAY_NAME} is properly installed."
            ) from e

        # Only generate .env.example file if it doesn't exist
        env_example_path = self.project_dir / ".env.example"
        if not env_example_path.exists():
            try:
                run(
                    [PKG_NAME, "generate", "-f", "env", "-y"],
                    cwd=self.project_dir,
                    check=True,
                    capture_output=True,
                )
                # Track the created file
                self.tracker.track(env_example_path)
            except CalledProcessError as e:
                error_msg = e.stderr.decode() if e.stderr else str(e)
                raise IOError(f"Failed to generate .env file: {error_msg}") from e
            except FileNotFoundError as e:
                raise IOError(
                    f"Command '{PKG_NAME}' not found. Ensure {PKG_DISPLAY_NAME} is properly installed."
                ) from e
        else:
            self.console.print("[dim].env.example already exists, skipping[/dim]")

    def _create_home_app(self) -> None:
        """Create the default home application."""
        home_creator = _HomeAppCreator(self.project_dir, self.writer, self.templates, self.console)
        home_creator.create()

    def _show_next_steps(self, preset: PresetType) -> None:
        """Display next steps for the user after successful initialization.

        Args:
            preset: The preset that was used.
        """
        from rich.panel import Panel

        next_steps = [
            "1. Install dependencies: [bold cyan]uv sync[/bold cyan]",
            "2. Copy [bold].env.example[/bold] to [bold].env[/bold] and configure",
        ]

        if preset == PresetType.VERCEL:
            next_steps.append(
                "3. Configure Vercel blob token in [bold]pyproject.toml[/bold] or [bold].env[/bold]"
            )
            next_steps.append("4. Run development server: [bold cyan]djx runserver[/bold cyan]")
        else:
            next_steps.append("3. Run development server: [bold cyan]djx runserver[/bold cyan]")

        panel = Panel(
            "\n".join(next_steps),
            title=f"[bold green]✓ {PKG_DISPLAY_NAME} project initialized successfully![/bold green]",
            border_style="green",
            padding=(1, 2),
        )

        self.console.print("\n")
        self.console.print(panel)

    def create(self, preset: str | None = None, force: bool = False) -> ExitCode:
        """Execute the full project initialization workflow.

        Args:
            preset: Optional preset to use without prompting.
            force: Skip directory validation.

        Returns:
            ExitCode indicating success or failure.
        """
        try:
            # Validate directory is empty or acceptable
            self._validate_directory(force=force)

            # Get and validate preset choice
            chosen_preset = self._get_preset_choice(preset)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True,
            ) as progress:
                # Create core configuration files
                task = progress.add_task("Creating project files...", total=None)
                self._create_core_files(chosen_preset)
                progress.update(task, completed=True)

                # Configure preset-specific files
                task = progress.add_task("Configuring preset files...", total=None)
                self._configure_preset_files_and_env_example(chosen_preset)
                progress.update(task, completed=True)

                # Create default app
                task = progress.add_task("Creating home app...", total=None)
                self._create_home_app()
                progress.update(task, completed=True)

            self._show_next_steps(chosen_preset)
            return ExitCode.SUCCESS

        except KeyboardInterrupt:
            self.tracker.cleanup_all()
            self.console.print(
                "\n[yellow]Project initialization cancelled. Cleaned up partial files.[/yellow]"
            )
            return ExitCode.ERROR

        except ProjectInitializationError as e:
            # User declined to proceed - no cleanup needed since nothing was created
            self.console.print(f"[yellow]{e}[/yellow]")
            return ExitCode.ERROR

        except ValueError as e:
            self.tracker.cleanup_all()
            self.console.print(
                f"[red]Configuration error:[/red] {e}\n[yellow]Cleaned up partial files.[/yellow]"
            )
            return ExitCode.ERROR

        except (IOError, PermissionError) as e:
            self.tracker.cleanup_all()
            self.console.print(
                f"[red]File system error:[/red] {e}\n[yellow]Cleaned up partial files.[/yellow]"
            )
            return ExitCode.ERROR

        except Exception as e:
            self.tracker.cleanup_all()
            self.console.print(
                f"[red]Unexpected error during initialization:[/red] {e}\n"
                f"[yellow]Cleaned up partial files.[/yellow]"
            )
            return ExitCode.ERROR


# ============================================================================
# Public API
# ============================================================================


def initialize(preset: str | None = None, force: bool = False) -> ExitCode:
    """Main entry point for project initialization.

    Creates a new project with the specified preset configuration.

    Args:
        preset: Optional preset to use without prompting.
            Available presets: 'default', 'vercel'.
        force: Skip directory validation and proceed even if directory is not empty.

    Returns:
        ExitCode.SUCCESS if initialization completed successfully,
        ExitCode.ERROR otherwise.

    Example:
        >>> initialize(preset="vercel")
        >>> initialize(force=True)
    """
    return _ProjectInitializer(PROJECT_DIR).create(preset=preset, force=force)
