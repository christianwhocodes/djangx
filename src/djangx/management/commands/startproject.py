"""Project initialization module for creating new projects.

This module handles the complete workflow of creating a new project with:
- Multiple preset configurations (default, Vercel, etc.)
- Multiple database backends (SQLite, PostgreSQL)
- Flexible PostgreSQL configuration methods
- Comprehensive validation and error handling
- File rollback on errors

==============================================================================
ARCHITECTURE OVERVIEW
==============================================================================

The module is organized into several key classes:

1. **Configuration & Templates** (_ProjectDependencies, _TemplateManager)
   - Manages dependency lists for different configurations
   - Generates file content from templates

2. **File Management** (_FileTracker, _ProjectFileWriter)
   - Tracks created files for rollback on errors
   - Handles file creation with existence checks

3. **App Creation** (_HomeAppCreator)
   - Creates the default 'home' application
   - Sets up templates and static files

4. **Main Orchestrator** (_ProjectInitializer)
   - Coordinates the entire initialization workflow
   - Validates configurations and handles errors

==============================================================================
INITIALIZATION FLOW
==============================================================================

When initialize() is called, the following sequence occurs:

┌─────────────────────────────────────────────────────────────┐
│ 1. DIRECTORY VALIDATION (unless --force)                    │
│    - Check if directory is empty or contains only safe items│
│    - Prompt user for confirmation if non-safe items exist   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. CONFIGURATION SELECTION                                  │
│    - Get preset choice (CLI flag or interactive prompt)     │
│    - Get database choice (CLI flag or interactive prompt)   │
│    - Get PG config method if PostgreSQL selected            │
│    - Validate all combinations using maps.py validators     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. CORE FILE CREATION                                       │
│    - Generate pyproject.toml with dependencies              │
│    - Create .gitignore and README.md                        │
│    - Track all created files for potential rollback         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. HOME APP CREATION                                        │
│    - Run startapp command                                   │
│    - Create urls.py and views.py                            │
│    - Set up template and static file structure              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. PRESET-SPECIFIC CONFIGURATION                            │
│    - Generate preset-specific files (e.g., vercel.json)     │
│    - Create .env.example with appropriate variables         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. SUCCESS DISPLAY                                          │
│    - Show next steps with context-specific instructions     │
│    - Include relevant documentation links                   │
└─────────────────────────────────────────────────────────────┘

If ANY step fails, all created files are automatically cleaned up via
the _FileTracker rollback mechanism.

==============================================================================
VALIDATION STRATEGY
==============================================================================

Validation occurs at TWO levels:

1. **CLI-Level Validation** (in cli.py)
   - Validates flag combinations before initialization begins
   - Example: --preset vercel with --database sqlite3
   - Provides immediate feedback without file creation

2. **Prompt-Level Validation** (in this module)
   - Validates interactive user choices
   - Ensures configuration compatibility using maps.py
   - Occurs during the initialization workflow

Both levels use the same validation functions from maps.py, ensuring
consistency between CLI and interactive modes.
"""

from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from pathlib import Path
from sys import argv
from typing import Final

from christianwhocodes.core import ExitCode
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt

from ... import PACKAGE, PROJECT
from ..enums import DatabaseEnum, PresetEnum
from ..settings import DATABASE_PRESETS, PG_CONFIG_PRESETS, STARTPROJECT_PRESETS
from ..utils import (
    validate_pg_config_compatibility,
    validate_preset_database_compatibility,
)

__all__: list[str] = ["handle_startproject"]

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
    "README",
    "README.md",
    "README.txt",
}


@dataclass(frozen=True)
class _ProjectDependencies:
    """Manages project dependencies for different configurations.

    This class centralizes dependency management, making it easy to see what
    packages are required for each configuration type.

    Attributes:
        base: Core dependencies required for all projects
        dev: Development dependencies (linters, formatters, etc.)
        postgresql: PostgreSQL-specific database drivers
        vercel: Vercel deployment dependencies
    """

    base: tuple[str, ...] = ("pillow>=12.1.0",)
    dev: tuple[str, ...] = ("djlint>=1.36.4", "ruff>=0.15.0")
    postgresql: tuple[str, ...] = ("psycopg[binary,pool]>=3.3.2",)
    vercel: tuple[str, ...] = ("vercel>=0.3.8",)

    def get_for_config(self, preset: PresetEnum, database: DatabaseEnum) -> list[str]:
        """Get complete dependency list for a specific configuration.

        This method combines base dependencies with configuration-specific ones,
        using the DATABASE_PRESETS and STARTPROJECT_PRESETS mappings to determine
        what's needed.

        Args:
            preset: The preset type (from STARTPROJECT_PRESETS mapping)
            database: The database backend (from DATABASE_PRESETS mapping)

        Returns:
            Complete list of dependency strings including version constraints.

        Example:
            >>> deps = _ProjectDependencies()
            >>> deps.get_for_config(PresetType.VERCEL, DatabaseBackend.POSTGRESQL)
            ['pillow>=12.1.0', 'psycopg[binary,pool]>=3.3.2', 'vercel>=0.3.8']
        """
        deps = list(self.base)
        deps.append(f"{PACKAGE.name}>={PACKAGE.version}")

        # Add database-specific dependencies using DATABASE_PRESETS mapping
        db_config = DATABASE_PRESETS[database]
        deps.extend(db_config.dependencies)

        # Add preset-specific dependencies using STARTPROJECT_PRESETS mapping
        preset_config = STARTPROJECT_PRESETS[preset]
        deps.extend(preset_config.dependencies)

        return deps


class _TemplateManager:
    """Manages all template content for project initialization.

    This class generates file content from templates. Each method corresponds
    to a specific file type that needs to be created during initialization.

    The templates are dynamic and can incorporate configuration-specific
    details (database settings, preset requirements, etc.).
    """

    @staticmethod
    def gitignore() -> str:
        """Generate .gitignore content.

        Returns standard .gitignore patterns for Python/Django projects,
        including database files, virtual environments, and IDE files.
        """
        return f"""
# Python-generated files
__pycache__/
*.py[oc]
build/
dist/
wheels/
*.egg-info

# Virtual environments
/.venv/
venv/
env/

# Ruff cache
/.ruff_cache/

# Temporary files
/.tmp/

# Static and media files
/public/

# Environment variables files
/.env
.env.local

# {DatabaseEnum.SQLITE3.value.capitalize()} database file
/db.{DatabaseEnum.SQLITE3.value}

# PostgreSQL service files (if using local config)
.pg_service.conf
pgpass.conf

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
""".strip()

    @staticmethod
    def readme() -> str:
        """Generate README.md content with getting started instructions."""
        return f"""
# {PROJECT.init_name}

A new project built with {PACKAGE.display_name}.

## Getting Started

1. Install dependencies: `uv sync`
2. Copy `.env.example` to `.env` and configure your environment variables
3. Run migrations: `uv run {PACKAGE.name} migrate`
4. Run development server: `uv run {PACKAGE.name} runserver`

## Development

- Format code: `uv run ruff format .`
- Lint code: `uv run ruff check .`
- Check templates: `uv run djlint --check .`

## Learn More

Visit the {PACKAGE.display_name} documentation to learn more about building with this framework.
""".strip()

    @staticmethod
    def pyproject_toml(
        preset: PresetEnum,
        database: DatabaseEnum,
        dependencies: list[str],
        use_postgres_env_vars: bool = False,
    ) -> str:
        """Generate pyproject.toml with configuration-specific settings.

        This template incorporates settings based on the chosen preset and
        database backend, using configuration from the mappings.

        Args:
            preset: Project preset type
            database: Database backend choice
            dependencies: List of all required dependencies
            use_postgres_env_vars: Whether to use env vars for PostgreSQL

        Returns:
            Complete pyproject.toml file content.
        """
        deps = _ProjectDependencies()
        deps_formatted = ",\n    ".join(f'"{dep}"' for dep in dependencies)
        dev_deps_formatted = ",\n    ".join(f'"{dep}"' for dep in deps.dev)

        # Build tool configuration based on mappings
        tool_config_parts: list[str] = []

        # Database configuration (from DATABASE_PRESETS)
        if database == DatabaseEnum.POSTGRESQL:
            tool_config_parts.append(
                f'db = {{ backend = "{DatabaseEnum.POSTGRESQL.value}", '
                f"use-env-vars = {str(use_postgres_env_vars).lower()} }}"
            )

        # Storage configuration (preset-specific from STARTPROJECT_PRESETS)
        if preset == PresetEnum.VERCEL:
            tool_config_parts.append(
                'storage = { backend = "vercel", '
                'blob-token = "keep-your-vercel-blob-token-secret-in-env" }'
            )

        # Format the tool config section
        tool_config = ""
        if tool_config_parts:
            tool_config = "\n" + "\n".join(tool_config_parts) + "\n"

        return f"""[project]
name = "{PROJECT.init_name}"
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

[tool.{PACKAGE.name}]{tool_config}
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
        """Generate home app index.html template content."""
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
        """Generate Tailwind CSS configuration and base styles."""
        return f"""@import "tailwindcss";

/* =============================================================================
   SOURCE FILES
   ============================================================================= */
@source "../../../../.venv/**/{PACKAGE.name}/ui/templates/ui/**/*.html";
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
    """Tracks files and directories created during initialization for rollback.

    This class implements the rollback mechanism that ensures clean failure handling.
    If initialization fails at any point, all created files and directories are
    automatically removed.

    The tracking happens in creation order, and cleanup happens in reverse order,
    ensuring child files are deleted before parent directories.
    """

    def __init__(self):
        """Initialize an empty file tracker."""
        self._created_paths: list[Path] = []

    def track(self, path: Path) -> None:
        """Track a created file or directory for potential rollback.

        Args:
            path: The filesystem path that was created.
        """
        if path not in self._created_paths:
            self._created_paths.append(path)

    def cleanup_all(self) -> None:
        """Remove all tracked files and directories in reverse creation order.

        This method is called when initialization fails. It performs best-effort
        cleanup, not raising exceptions if individual deletions fail.
        """
        from shutil import rmtree

        # Reverse order ensures files are removed before their parent directories
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
    """Handles file writing operations with existence checks and tracking.

    This class centralizes all file I/O operations, ensuring:
    - Files are only created if they don't exist (idempotent)
    - All created files are tracked for rollback
    - Consistent error handling across file operations
    """

    def __init__(self, project_dir: Path, console: Console, tracker: _FileTracker):
        """Initialize the file writer.

        Args:
            project_dir: Root directory for the project
            console: Rich console for user feedback
            tracker: File tracker for rollback support
        """
        self.project_dir = project_dir
        self.console = console
        self.tracker = tracker

    def write_if_not_exists(self, filename: str, content: str) -> bool:
        """Write content to a file in the project directory if it doesn't exist.

        Args:
            filename: Name of the file to create (relative to project_dir)
            content: Content to write to the file

        Returns:
            True if file was created, False if it already existed.

        Raises:
            IOError: If file cannot be written.
            PermissionError: If lacking write permissions.
        """
        file_path = self.project_dir / filename

        if file_path.exists():
            return False

        file_path.write_text(content.strip() + "\n", encoding="utf-8")
        self.tracker.track(file_path)
        return True

    def write_to_path_if_not_exists(self, path: Path, content: str) -> bool:
        """Write content to a specific path if it doesn't exist.

        Args:
            path: Full filesystem path to the file
            content: Content to write to the file

        Returns:
            True if file was created, False if it already existed.

        Raises:
            IOError: If file cannot be written.
            PermissionError: If lacking write permissions.
        """
        if path.exists():
            return False

        path.write_text(content.strip() + "\n", encoding="utf-8")
        self.tracker.track(path)
        return True

    def ensure_dir(self, path: Path) -> bool:
        """Ensure a directory exists, creating it if necessary.

        Args:
            path: Directory path to create

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
    """Creates the default 'home' application with all necessary files.

    This class handles the creation of the starter application that comes with
    every new project. It sets up:
    - app structure (via startapp command)
    - URL routing configuration
    - View classes
    - Template directory structure
    - Static file structure with Tailwind CSS
    """

    def __init__(
        self,
        project_dir: Path,
        writer: _ProjectFileWriter,
        templates: _TemplateManager,
        console: Console,
    ):
        """Initialize the home app creator.

        Args:
            project_dir: Root project directory
            writer: File writer instance for creating files
            templates: Template manager for generating content
            console: Rich console for user feedback
        """
        self.project_dir = project_dir
        self.writer = writer
        self.templates = templates
        self.console = console

    def create(self) -> None:
        """Execute the complete home app creation workflow.

        Flow:
        1. Check if app already exists (idempotent operation)
        2. Create app structure via startapp
        3. Create custom URLs and views
        4. Set up template directory and files
        5. Set up static file directory and CSS
        """
        # Check if home app already exists
        if PROJECT.home_app_exists:
            self.console.print(
                "[yellow]Home app directory already exists, skipping app creation[/yellow]"
            )
            return

        # Create the app structure
        self._create_app_structure()

        # Create app files
        self._create_urls()
        self._create_views()
        self._create_templates()
        self._create_static_files()

    def _create_app_structure(self) -> None:
        """Create the basic app structure using the startapp command."""
        from django.core.management import call_command

        try:
            call_command("startapp", "home")
            # Track the created directory for rollback
            self.writer.tracker.track(PROJECT.home_app_dir)
        except Exception as e:
            raise IOError(f"Failed to create home app: {e}") from e

    def _create_urls(self) -> None:
        """Create custom urls.py for the home app."""
        urls_path = PROJECT.home_app_dir / "urls.py"
        if self.writer.write_to_path_if_not_exists(urls_path, self.templates.home_urls()):
            pass  # File was created
        else:
            self.console.print("[dim]urls.py already exists, skipping[/dim]")

    def _create_views(self) -> None:
        """Create custom views.py for the home app."""
        views_path = PROJECT.home_app_dir / "views.py"
        # Only overwrite if it's the default startapp content
        if views_path.exists():
            content = views_path.read_text(encoding="utf-8")
            # Check if it's the default views.py (very minimal content)
            if len(content.strip()) < 100:
                views_path.write_text(self.templates.home_views().strip() + "\n", encoding="utf-8")
        else:
            self.writer.write_to_path_if_not_exists(views_path, self.templates.home_views())

    def _create_templates(self) -> None:
        """Create template directory structure and HTML files."""
        templates_dir = PROJECT.home_app_dir / "templates" / "home"
        self.writer.ensure_dir(templates_dir)

        index_path = templates_dir / "index.html"
        self.writer.write_to_path_if_not_exists(index_path, self.templates.home_index_html())

    def _create_static_files(self) -> None:
        """Create static file directory structure and CSS files."""
        static_dir = PROJECT.home_app_dir / "static" / "home" / "css"
        self.writer.ensure_dir(static_dir)

        css_path = static_dir / "tailwind.css"
        self.writer.write_to_path_if_not_exists(css_path, self.templates.tailwind_css())


# ============================================================================
# Main Initializer
# ============================================================================


class ProjectInitializationError(Exception):
    """Raised when project initialization fails due to user cancellation or invalid state."""

    pass


class _ProjectInitializer:
    """Main orchestrator for project initialization workflow.

    This class coordinates the entire initialization process, handling:
    - Directory validation
    - User prompts for configuration selection
    - Validation of configuration combinations
    - File creation and tracking
    - Error handling and rollback
    - Success message display

    The initializer uses composition, delegating specific tasks to specialized
    classes while maintaining overall workflow control.
    """

    def __init__(
        self,
        project_dir: Path,
        dependencies: _ProjectDependencies | None = None,
        templates: _TemplateManager | None = None,
        console: Console | None = None,
    ):
        """Initialize the project initializer with configuration.

        Args:
            project_dir: Directory where project will be created
            dependencies: Dependency manager (uses default if None)
            templates: Template manager (uses default if None)
            console: Rich console for output (creates new if None)
        """
        self.project_dir = Path(project_dir)
        self.dependencies = dependencies or _ProjectDependencies()
        self.templates = templates or _TemplateManager()
        self.console = console or Console()
        self.tracker = _FileTracker()
        self.writer = _ProjectFileWriter(self.project_dir, self.console, self.tracker)

    def _validate_directory(self, force: bool = False) -> None:
        """Validate that the directory is suitable for initialization.

        Checks for existing files that might conflict with initialization.
        Safe items (like .git, LICENSE) are allowed without prompting.

        Args:
            force: Skip all validation and proceed regardless

        Raises:
            ProjectInitializationError: If directory is unsuitable and user declines
        """
        if force:
            return

        existing_items = list(self.project_dir.iterdir())
        if not existing_items:
            return

        # Filter out safe items (VCS, LICENSE, README, etc.)
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
            f"Initialize {PACKAGE.display_name} project anyway? "
            "This will skip existing files and create new ones",
            default=False,
            console=self.console,
        )

        if not should_proceed:
            raise ProjectInitializationError("Initialization cancelled by user.")

    def _get_preset_choice(self, preset: str | None = None) -> PresetEnum:
        """Get and validate the preset choice.

        Uses STARTPROJECT_PRESETS mapping to validate and provide choices.

        Args:
            preset: CLI-provided preset (skips prompt if provided)

        Returns:
            Validated PresetType enum value

        Raises:
            ValueError: If provided preset is invalid
        """
        if preset:
            try:
                return PresetEnum(preset)
            except ValueError:
                valid_presets = [p.value for p in PresetEnum]
                raise ValueError(
                    f"Invalid preset '{preset}'. Must be one of: {', '.join(valid_presets)}"
                ) from None

        # Interactive prompt with descriptions from STARTPROJECT_PRESETS
        self.console.print("\n[bold]Choose a project preset:[/bold]")
        for preset_type in PresetEnum:
            config = STARTPROJECT_PRESETS[preset_type]
            self.console.print(f"  • [cyan]{preset_type.value}[/cyan]: {config.description}")

        choice = Prompt.ask(
            "\nYour choice",
            choices=[p.value for p in PresetEnum],
            default=PresetEnum.DEFAULT.value,
            console=self.console,
        )
        return PresetEnum(choice)

    def _get_postgres_config_choice(
        self, preset: PresetEnum, pg_env_vars: bool | None = None
    ) -> bool:
        """Get PostgreSQL configuration method choice.

        Uses PG_CONFIG_PRESETS mapping to provide options and validate choices.

        Args:
            preset: Current preset (Vercel requires env vars)
            pg_env_vars: CLI-provided flag (skips prompt if provided)

        Returns:
            True for environment variables, False for service files
        """
        # Vercel requires environment variables (no filesystem access)
        preset_config = STARTPROJECT_PRESETS[preset]
        if preset_config.required_pg_config is not None:
            return preset_config.required_pg_config

        # If flag provided, use it
        if pg_env_vars is not None:
            return pg_env_vars

        # Interactive prompt with descriptions from PG_CONFIG_PRESETS
        self.console.print("\n[bold]PostgreSQL Configuration Method:[/bold]")
        for use_env_vars, method in PG_CONFIG_PRESETS.items():
            self.console.print(f"  • [cyan]{method.name}[/cyan]: {method.description}")

        use_env_vars = Confirm.ask(
            "\nUse environment variables?",
            default=True,
            console=self.console,
        )

        return use_env_vars

    def _get_database_choice(
        self, preset: PresetEnum, database: str | None = None, pg_env_vars: bool | None = None
    ) -> tuple[DatabaseEnum, bool]:
        """Get and validate database choice with PostgreSQL configuration.

        Uses DATABASE_PRESETS mapping for validation and STARTPROJECT_PRESETS for
        compatibility checking.

        Args:
            preset: Current preset (may restrict database choices)
            database: CLI-provided database (skips prompt if provided)
            pg_env_vars: CLI-provided PG config flag

        Returns:
            Tuple of (database_backend, use_postgres_env_vars)

        Raises:
            ValueError: If database is invalid or incompatible with preset
        """
        preset_config = STARTPROJECT_PRESETS[preset]

        # Check if preset requires a specific database
        if preset_config.required_database is not None:
            if database and database != preset_config.required_database.value:
                raise ValueError(
                    f"{preset_config.name} preset requires "
                    f"{preset_config.required_database.value} database (got: {database})"
                )
            required_db = preset_config.required_database
            use_env_vars = self._get_postgres_config_choice(preset, pg_env_vars)
            return required_db, use_env_vars

        # If database explicitly provided, validate it
        if database:
            try:
                db_backend = DatabaseEnum(database)
            except ValueError:
                valid_databases = [db.value for db in DatabaseEnum]
                raise ValueError(
                    f"Invalid database '{database}'. Must be one of: {', '.join(valid_databases)}"
                ) from None

            # Validate compatibility with preset
            is_valid, error_msg = validate_preset_database_compatibility(preset, db_backend)
            if not is_valid:
                raise ValueError(error_msg)

            # Get PostgreSQL config method if applicable
            db_config = DATABASE_PRESETS[db_backend]
            use_env_vars = (
                self._get_postgres_config_choice(preset, pg_env_vars)
                if db_config.requires_pg_config
                else False
            )
            return db_backend, use_env_vars

        # Interactive prompt with descriptions from DATABASE_PRESETS
        self.console.print("\n[bold]Choose a database backend:[/bold]")
        for db_backend in DatabaseEnum:
            config = DATABASE_PRESETS[db_backend]
            self.console.print(f"  • [cyan]{db_backend.value}[/cyan]: {config.description}")

        choice = Prompt.ask(
            "\nYour choice",
            choices=[db.value for db in DatabaseEnum],
            default=DatabaseEnum.SQLITE3.value,
            console=self.console,
        )
        db_backend = DatabaseEnum(choice)

        # Get PostgreSQL config method if applicable
        db_config = DATABASE_PRESETS[db_backend]
        use_env_vars = (
            self._get_postgres_config_choice(preset, pg_env_vars)
            if db_config.requires_pg_config
            else False
        )
        return db_backend, use_env_vars

    def _create_core_files(
        self, preset: PresetEnum, database: DatabaseEnum, use_postgres_env_vars: bool
    ) -> None:
        """Create core project configuration files.

        Creates pyproject.toml, .gitignore, and README.md with configuration-specific
        content using the template manager.

        Args:
            preset: Project preset type
            database: Database backend choice
            use_postgres_env_vars: PostgreSQL configuration method

        Raises:
            IOError: If files cannot be created
        """
        dependencies = self.dependencies.get_for_config(preset, database)

        files_to_create = {
            "pyproject.toml": self.templates.pyproject_toml(
                preset, database, dependencies, use_postgres_env_vars
            ),
            ".gitignore": self.templates.gitignore(),
            "README.md": self.templates.readme(),
        }

        for filename, content in files_to_create.items():
            if self.writer.write_if_not_exists(filename, content):
                pass  # File was created
            else:
                self.console.print(f"[dim]{filename} already exists, skipping[/dim]")

    def _configure_preset_files_and_env_example(self, preset: PresetEnum) -> None:
        """Generate preset-specific files using the framework's generate command.

        Uses STARTPROJECT_PRESETS mapping to determine what files need to be generated.

        Args:
            preset: Project preset type

        Raises:
            IOError: If file generation fails
        """
        from subprocess import CalledProcessError, run

        try:
            # Generate preset-specific files
            match preset:
                case PresetEnum.VERCEL:
                    # Generate vercel.json if it doesn't exist
                    if not (self.project_dir / "vercel.json").exists():
                        run(
                            [PACKAGE.name, "generate", "-f", "vercel", "-y"],
                            cwd=self.project_dir,
                            check=True,
                            capture_output=True,
                        )
                        self.tracker.track(self.project_dir / "vercel.json")
                    else:
                        self.console.print("[dim]vercel.json already exists, skipping[/dim]")

                    # Generate api/server.py if it doesn't exist
                    server_path = self.project_dir / "api" / "server.py"
                    if not server_path.exists():
                        run(
                            [PACKAGE.name, "generate", "-f", "server", "-y"],
                            cwd=self.project_dir,
                            check=True,
                            capture_output=True,
                        )
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
                f"Command '{PACKAGE.name}' not found. Ensure {PACKAGE.display_name} is properly installed."
            ) from e

        # Generate .env.example file if it doesn't exist
        env_example_path = self.project_dir / ".env.example"
        if not env_example_path.exists():
            try:
                run(
                    [PACKAGE.name, "generate", "-f", "env", "-y"],
                    cwd=self.project_dir,
                    check=True,
                    capture_output=True,
                )
                self.tracker.track(env_example_path)
            except CalledProcessError as e:
                error_msg = e.stderr.decode() if e.stderr else str(e)
                raise IOError(f"Failed to generate .env file: {error_msg}") from e
            except FileNotFoundError as e:
                raise IOError(
                    f"Command '{PACKAGE.name}' not found. Ensure {PACKAGE.display_name} is properly installed."
                ) from e
        else:
            self.console.print("[dim].env.example already exists, skipping[/dim]")

    def _create_home_app(self) -> None:
        """Create the default 'home' application."""
        home_creator = _HomeAppCreator(self.project_dir, self.writer, self.templates, self.console)
        home_creator.create()

    def _show_next_steps(
        self, preset: PresetEnum, database: DatabaseEnum, use_postgres_env_vars: bool
    ) -> None:
        """Display context-specific next steps after successful initialization.

        Uses configuration mappings to provide relevant instructions and
        documentation links based on the chosen configuration.

        Args:
            preset: Project preset that was used
            database: Database backend that was chosen
            use_postgres_env_vars: PostgreSQL configuration method
        """
        from rich.panel import Panel

        next_steps = [
            "1. Install dependencies: [bold cyan]uv sync[/bold cyan]",
            "2. Copy [bold].env.example[/bold] to [bold].env[/bold] and configure",
        ]

        step_num = 3

        # Database-specific instructions using DATABASE_PRESETS
        db_config = DATABASE_PRESETS[database]
        if db_config.requires_pg_config:
            pg_method = PG_CONFIG_PRESETS[use_postgres_env_vars]
            if use_postgres_env_vars:
                next_steps.append(
                    f"{step_num}. Configure PostgreSQL connection in [bold].env[/bold]"
                )
            else:
                files_list = " and [bold]".join([f"[bold]{f}" for f in pg_method.files_required])
                next_steps.append(
                    f"{step_num}. Configure PostgreSQL connection using {files_list}[/bold] files"
                )
            step_num += 1

        # Preset-specific instructions using STARTPROJECT_PRESETS
        preset_config = STARTPROJECT_PRESETS[preset]
        if preset == PresetEnum.VERCEL:
            next_steps.append(f"{step_num}. Configure Vercel blob token in [bold].env[/bold]")
            step_num += 1

        next_steps.extend(
            [
                f"{step_num}. Run migrations: [bold cyan]uv run {PACKAGE.name} migrate[/bold cyan]",
                f"{step_num + 1}. Run development server: [bold cyan]uv run {PACKAGE.name} runserver[/bold cyan]",
            ]
        )

        # Build panel content
        content = "\n".join(next_steps)

        # Add relevant documentation links
        learn_more_links: list[str] = []

        # Database documentation
        if db_config.learn_more_url:
            learn_more_links.append(f"   {db_config.learn_more_url}")

        # PostgreSQL config documentation
        if db_config.requires_pg_config:
            pg_method = PG_CONFIG_PRESETS[use_postgres_env_vars]
            if pg_method.learn_more_url:
                learn_more_links.append(f"   {pg_method.learn_more_url}")

        # Preset documentation
        if preset_config.learn_more_url:
            learn_more_links.append(f"   {preset_config.learn_more_url}")

        if learn_more_links:
            content += "\n\n"
            content += "[dim italic]💡 Learn more:[/dim italic]\n"
            content += "[dim cyan]" + "\n".join(learn_more_links) + "[/dim cyan]"

        panel = Panel(
            content,
            title=f"[bold green]✓ {PACKAGE.display_name} project initialized successfully![/bold green]",
            border_style="green",
            padding=(1, 2),
        )

        self.console.print("\n")
        self.console.print(panel)

    def create(
        self,
        preset: str | None = None,
        database: str | None = None,
        pg_env_vars: bool | None = None,
        force: bool = False,
    ) -> ExitCode:
        """Execute the complete project initialization workflow.

        This is the main entry point that orchestrates all initialization steps.
        See module docstring for detailed flow diagram.

        Args:
            preset: Optional preset to use (skips interactive prompt)
            database: Optional database backend (skips interactive prompt)
            pg_env_vars: Optional PG config flag (skips interactive prompt)
            force: Skip directory validation

        Returns:
            ExitCode.SUCCESS if initialization completed successfully,
            ExitCode.ERROR otherwise.
        """
        try:
            # Step 1: Validate directory
            self._validate_directory(force=force)

            # Step 2: Get configuration choices with validation
            chosen_preset = self._get_preset_choice(preset)
            chosen_database, use_postgres_env_vars = self._get_database_choice(
                chosen_preset, database, pg_env_vars
            )

            # Steps 3-5: Create files with progress feedback
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True,
            ) as progress:
                # Step 3: Core files
                task = progress.add_task("Creating project files...", total=None)
                self._create_core_files(chosen_preset, chosen_database, use_postgres_env_vars)
                progress.update(task, completed=True)

                # Step 4: Home app
                task = progress.add_task("Creating home app...", total=None)
                self._create_home_app()
                progress.update(task, completed=True)

                # Step 5: Preset-specific files
                task = progress.add_task("Configuring preset files...", total=None)
                self._configure_preset_files_and_env_example(chosen_preset)
                progress.update(task, completed=True)

            # Step 6: Display success message
            self._show_next_steps(chosen_preset, chosen_database, use_postgres_env_vars)
            return ExitCode.SUCCESS

        except KeyboardInterrupt:
            self.tracker.cleanup_all()
            self.console.print(
                "\n[yellow]Project initialization cancelled. Cleaned up partial files.[/yellow]"
            )
            return ExitCode.ERROR

        except ProjectInitializationError as e:
            # User declined - no cleanup needed since nothing was created
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


def handle_startproject() -> ExitCode:
    f"""Handle the 'startproject' command with comprehensive argument parsing and validation.

    This function is the bridge between CLI arguments and the project initialization logic.
    It performs several key responsibilities:

    1. **Argument Parsing**: Defines and parses all CLI flags for project creation
    2. **Validation**: Validates argument combinations at the CLI level
    3. **Translation**: Converts CLI flags to function parameters
    4. **Error Reporting**: Provides clear error messages for invalid combinations

    The validation happens in two stages:
    - CLI-level validation (this function): Catches incompatible flag combinations
    - Prompt-level validation (in startproject.py): Validates interactive choices

    Returns:
        ExitCode from the initialize function (SUCCESS or ERROR).

    Raises:
        SystemExit: Via parser.error() for invalid argument combinations.

    Flow:
        1. Create ArgumentParser with all available flags
        2. Parse sys.argv[2:] (everything after the command name - startproject/init/new )
        3. Validate preset-database compatibility
        4. Validate preset-pg_config compatibility
        5. Convert mutually-exclusive flags to single parameter
        6. Call initialize() with validated parameters

    Example CLI calls:
        $ {PACKAGE.name} startproject --preset vercel  # Auto-selects PostgreSQL + env vars
        $ {PACKAGE.name} startproject --database postgresql --pg-env-vars
        $ {PACKAGE.name} startproject --preset default --database sqlite3
        $ {PACKAGE.name} startproject --database sqlite3  # Auto-selects 'default' preset
        $ {PACKAGE.name} startproject --force
    """

    # ========================================================================
    # Argument Parser Setup
    # ========================================================================

    parser = ArgumentParser(
        prog=f"{PACKAGE.name} startproject",
        description=f"Initialize a new {PACKAGE.display_name} project",
    )

    # ------------------------------------------------------------------------
    # Preset Selection Flag
    # ------------------------------------------------------------------------
    # Determines the project template/configuration to use
    # Maps to: PresetType enum and STARTPROJECT_PRESETS mapping

    preset_help_lines = ["Project preset to use (skips interactive prompt). Options:"]
    for preset_type in PresetEnum:
        config = STARTPROJECT_PRESETS[preset_type]
        preset_help_lines.append(f"  • {preset_type.value}: {config.description}")

    parser.add_argument(
        "--preset",
        choices=[p.value for p in PresetEnum],
        help=" ".join(preset_help_lines),
        metavar="PRESET",
    )

    # ------------------------------------------------------------------------
    # Database Backend Flag
    # ------------------------------------------------------------------------
    # Determines which database system to configure
    # Maps to: DatabaseBackend enum and DATABASE_PRESETS mapping

    db_help_lines = ["Database backend to use (skips interactive prompt). Options:"]
    for db_backend in DatabaseEnum:
        config = DATABASE_PRESETS[db_backend]
        db_help_lines.append(f"  • {db_backend.value}: {config.description}")
    db_help_lines.append(
        f"\nNote: {STARTPROJECT_PRESETS[PresetEnum.VERCEL].name} preset requires "
        f"{DatabaseEnum.POSTGRESQL.value}."
    )

    parser.add_argument(
        "--database",
        "--db",
        choices=[db.value for db in DatabaseEnum],
        help=" ".join(db_help_lines),
        metavar="DATABASE",
    )

    # ------------------------------------------------------------------------
    # PostgreSQL Configuration Method Flags (Mutually Exclusive)
    # ------------------------------------------------------------------------
    # Determines how PostgreSQL credentials are managed
    # Maps to: PG_CONFIG_PRESETS mapping
    # Only relevant when database=postgresql

    pg_config_group = parser.add_mutually_exclusive_group()

    env_vars_method = PG_CONFIG_PRESETS[True]
    pg_config_group.add_argument(
        env_vars_method.cli_flag,
        action="store_true",
        dest="pg_env_vars_flag",
        help=f"{env_vars_method.description} (skips interactive prompt)",
    )

    service_files_method = PG_CONFIG_PRESETS[False]
    pg_config_group.add_argument(
        service_files_method.cli_flag,
        action="store_true",
        dest="pg_service_files_flag",
        help=f"{service_files_method.description} (skips interactive prompt)",
    )

    # ------------------------------------------------------------------------
    # Force Flag
    # ------------------------------------------------------------------------
    # Bypasses directory validation checks

    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Skip directory validation and initialize even if directory is not empty",
    )

    # ========================================================================
    # Parse Arguments
    # ========================================================================
    # sys.argv structure: [script_name, command, *args]
    # Example: ['script_name', 'startproject', '--preset', 'vercel']
    # We parse from index 2 onwards to skip 'script_name' and 'startproject'

    args: Namespace = parser.parse_args(argv[2:])

    # ========================================================================
    # CLI-Level Validation and Auto-Configuration
    # ========================================================================
    # We validate incompatible combinations BEFORE calling initialize()
    # This provides immediate feedback at the CLI level

    # Convert string values to enum types for validation
    preset_enum = PresetEnum(args.preset) if args.preset else None
    database_enum = DatabaseEnum(args.database) if args.database else None

    # ------------------------------------------------------------------------
    # Auto-configure based on preset/database requirements
    # ------------------------------------------------------------------------
    # If database is sqlite3 but no preset specified, auto-select 'default'
    # since 'vercel' preset requires PostgreSQL. This skips the preset prompt.
    if not preset_enum and database_enum == DatabaseEnum.SQLITE3:
        preset_enum = PresetEnum.DEFAULT
        args.preset = PresetEnum.DEFAULT.value

    # If preset is vercel but no database specified, auto-select PostgreSQL
    # and environment variables config since Vercel requires both.
    if preset_enum == PresetEnum.VERCEL:
        if not database_enum:
            database_enum = DatabaseEnum.POSTGRESQL
            args.database = DatabaseEnum.POSTGRESQL.value
        # Auto-select env vars for PostgreSQL if no PG config method specified
        if not args.pg_env_vars_flag and not args.pg_service_files_flag:
            args.pg_env_vars_flag = True

    # ------------------------------------------------------------------------
    # Validate Preset-Database Compatibility
    # ------------------------------------------------------------------------
    if preset_enum and database_enum:
        is_valid, error_msg = validate_preset_database_compatibility(preset_enum, database_enum)
        if not is_valid:
            parser.error(error_msg)

    # ------------------------------------------------------------------------
    # Validate Preset-PostgreSQL Config Compatibility
    # ------------------------------------------------------------------------
    if preset_enum:
        # Check if user specified a PG config method
        if args.pg_env_vars_flag:
            is_valid, error_msg = validate_pg_config_compatibility(preset_enum, True)
            if not is_valid:
                parser.error(error_msg)
        elif args.pg_service_files_flag:
            is_valid, error_msg = validate_pg_config_compatibility(preset_enum, False)
            if not is_valid:
                parser.error(error_msg)

    # ========================================================================
    # Convert CLI Flags to Function Parameters
    # ========================================================================
    # The mutually-exclusive flags (--pg-env-vars, --pg-service-files) need
    # to be converted into a single Optional[bool] parameter:
    # - True: use environment variables
    # - False: use service files
    # - None: ask user interactively

    pg_env_vars_value: bool | None = None
    if args.pg_env_vars_flag:
        pg_env_vars_value = True
    elif args.pg_service_files_flag:
        pg_env_vars_value = False

    # ========================================================================
    # Call Initializer
    # ========================================================================
    return _ProjectInitializer(PROJECT.base_dir).create(
        preset=args.preset,  # str | None
        database=args.database,  # str | None
        pg_env_vars=pg_env_vars_value,  # bool | None
        force=args.force,  # bool
    )
