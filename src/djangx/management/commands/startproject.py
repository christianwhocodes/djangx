"""Project initialization command."""

from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from pathlib import Path
from sys import argv
from typing import Final

from christianwhocodes.core import ExitCode
from rich.console import Console
from rich.markup import escape
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt

from ... import PACKAGE, PROJECT
from ..enums import DatabaseEnum, PresetEnum
from ..settings import DATABASE_PRESETS, PG_CONFIG_PRESETS, STARTPROJECT_PRESETS
from ..validators import (
    validate_pg_config_compatibility,
    validate_preset_database_compatibility,
)

__all__: list[str] = ["handle_startproject"]

# ============================================================================
# Configuration & Templates
# ============================================================================

# VCS and common items that shouldn't prevent initialization
_SAFE_DIRECTORY_ITEMS: Final[set[str]] = {
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
    """Manages project dependencies for different configurations."""

    base: tuple[str, ...] = ("pillow>=12.1.0",)
    dev: tuple[str, ...] = ("djlint>=1.36.4", "ruff>=0.15.0")
    postgresql: tuple[str, ...] = ("psycopg[binary,pool]>=3.3.2",)
    vercel: tuple[str, ...] = ("vercel>=0.3.8",)

    def get_for_config(self, preset: PresetEnum, database: DatabaseEnum) -> list[str]:
        """Get the complete dependency list for a preset and database combination."""
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
    """Generates file content templates for project initialization."""

    @staticmethod
    def gitignore(database: DatabaseEnum) -> str:
        """Generate .gitignore content."""
        # Database-specific entries
        db_lines = ""
        if database == DatabaseEnum.SQLITE3:
            db_lines = f"""
# {DatabaseEnum.SQLITE3.value.capitalize()} database file
/db.{DatabaseEnum.SQLITE3.value}
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
{db_lines}
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
        """Generate README.md content."""
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
        """Generate pyproject.toml content."""
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
    def tailwindcss() -> str:
        """Generate TailwindCSS source file."""
        return f"""@import "tailwindcss";

/* =============================================================================
   SOURCE FILES
   ============================================================================= */
@source "../../../../.venv/**/{PACKAGE.name}/{PACKAGE.main_app_name}/templates/ui/**/*.html";
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
    """Tracks created files/dirs for rollback on failure."""

    def __init__(self):
        self._created_paths: list[Path] = []

    def track(self, path: Path) -> None:
        """Register a path for potential rollback."""
        if path not in self._created_paths:
            self._created_paths.append(path)

    def cleanup_all(self) -> None:
        """Remove all tracked paths in reverse creation order."""
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
    """Handles file creation with existence checks and rollback tracking."""

    def __init__(self, project_dir: Path, console: Console, tracker: _FileTracker):
        self.project_dir = project_dir
        self.console = console
        self.tracker = tracker

    def write_if_not_exists(self, filename: str, content: str) -> bool:
        """Write file in project dir if it doesn't already exist."""
        file_path = self.project_dir / filename

        if file_path.exists():
            return False

        file_path.write_text(content.strip() + "\n", encoding="utf-8")
        self.tracker.track(file_path)
        return True

    def write_to_path_if_not_exists(self, path: Path, content: str) -> bool:
        """Write to a specific path if it doesn't already exist."""
        if path.exists():
            return False

        path.write_text(content.strip() + "\n", encoding="utf-8")
        self.tracker.track(path)
        return True

    def ensure_dir(self, path: Path) -> bool:
        """Create directory if it doesn't exist."""
        if path.exists():
            return False

        path.mkdir(parents=True, exist_ok=True)
        self.tracker.track(path)
        return True


# ============================================================================
# Home App Creator
# ============================================================================


# Path to the bundled home app assets directory
_HOME_APP_ASSETS_DIR: Final[Path] = (
    Path(__file__).resolve().parent.parent / "assets" / "startproject" / "home"
)


class _HomeAppCreator:
    """Copies bundled home app assets into a new project."""

    def __init__(
        self,
        project_dir: Path,
        tracker: _FileTracker,
        console: Console,
    ):
        self.project_dir = project_dir
        self.tracker = tracker
        self.console = console

    def create(self) -> None:
        """Copy the home app from package assets to the project directory."""
        from shutil import copytree

        # Check if home app already exists
        if PROJECT.home_app_exists:
            self.console.print(
                "[yellow]Home app directory already exists, skipping app creation[/yellow]"
            )
            return

        if not _HOME_APP_ASSETS_DIR.exists():
            raise IOError(f"Home app assets directory not found: {_HOME_APP_ASSETS_DIR}")

        try:
            copytree(_HOME_APP_ASSETS_DIR, PROJECT.home_app_dir)
            self.tracker.track(PROJECT.home_app_dir)
        except Exception as e:
            raise IOError(f"Failed to copy home app assets: {e}") from e


# ============================================================================
# Main Initializer
# ============================================================================


class ProjectInitializationError(Exception):
    """Initialization failed due to cancellation or invalid state."""

    pass


class _ProjectInitializer:
    """Orchestrates the project initialization workflow."""

    def __init__(
        self,
        project_dir: Path,
        dependencies: _ProjectDependencies | None = None,
        templates: _TemplateManager | None = None,
        console: Console | None = None,
    ):
        self.project_dir = Path(project_dir)
        self.dependencies = dependencies or _ProjectDependencies()
        self.templates = templates or _TemplateManager()
        self.console = console or Console()
        self.tracker = _FileTracker()
        self.writer = _ProjectFileWriter(self.project_dir, self.console, self.tracker)

    def _validate_directory(self, force: bool = False) -> None:
        """Ensure the directory is suitable for initialization."""
        if force:
            return

        existing_items = list(self.project_dir.iterdir())
        if not existing_items:
            return

        # Filter out safe items (VCS, LICENSE, README, etc.)
        problematic_items = [
            item for item in existing_items if item.name not in _SAFE_DIRECTORY_ITEMS
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
        """Prompt for or validate the preset choice."""
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
        """Prompt for or resolve the PostgreSQL config method."""
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
        """Prompt for or validate the database choice and PG config method."""
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
        """Create pyproject.toml, .gitignore, and README.md."""
        dependencies = self.dependencies.get_for_config(preset, database)

        files_to_create = {
            "pyproject.toml": self.templates.pyproject_toml(
                preset, database, dependencies, use_postgres_env_vars
            ),
            ".gitignore": self.templates.gitignore(database),
            "README.md": self.templates.readme(),
        }

        for filename, content in files_to_create.items():
            if self.writer.write_if_not_exists(filename, content):
                pass  # File was created
            else:
                self.console.print(f"[dim]{filename} already exists, skipping[/dim]")

    def _configure_preset_files_and_env_example(self, preset: PresetEnum) -> None:
        """Generate preset-specific files and .env.example."""
        from os import environ
        from subprocess import CalledProcessError, run

        # Ensure subprocess uses UTF-8 to avoid encoding errors on Windows
        sub_env = {**environ, "PYTHONUTF8": "1"}

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
                            env=sub_env,
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
                            env=sub_env,
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
                    env=sub_env,
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
        home_creator = _HomeAppCreator(self.project_dir, self.tracker, self.console)
        home_creator.create()

    def _show_next_steps(
        self, preset: PresetEnum, database: DatabaseEnum, use_postgres_env_vars: bool
    ) -> None:
        """Display post-initialization instructions."""
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
        """Run the full project initialization workflow."""
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
            self.console.print(f"[yellow]{escape(str(e))}[/yellow]")
            return ExitCode.ERROR

        except ValueError as e:
            self.tracker.cleanup_all()
            self.console.print(
                f"[red]Configuration error:[/red] {escape(str(e))}\n[yellow]Cleaned up partial files.[/yellow]"
            )
            return ExitCode.ERROR

        except (IOError, PermissionError) as e:
            self.tracker.cleanup_all()
            self.console.print(
                f"[red]File system error:[/red] {escape(str(e))}\n[yellow]Cleaned up partial files.[/yellow]"
            )
            return ExitCode.ERROR

        except Exception as e:
            self.tracker.cleanup_all()
            self.console.print(
                f"[red]Unexpected error during initialization:[/red] {escape(str(e))}\n"
                f"[yellow]Cleaned up partial files.[/yellow]"
            )
            return ExitCode.ERROR


# ============================================================================
# Public API
# ============================================================================


def handle_startproject() -> ExitCode:
    """Parse CLI arguments and run project initialization."""
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
