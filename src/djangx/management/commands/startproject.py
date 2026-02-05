from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from christianwhocodes.core import ExitCode, Version

from ... import PKG_DISPLAY_NAME, PKG_NAME, PROJECT_DIR, PROJECT_INIT_NAME

__all__ = ["initialize"]

# ============================================================================
# Configuration & Templates
# ============================================================================


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
2. Run development server: `uv run djx runserver`
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
    def tailwind_css() -> str:
        """Generate Tailwind CSS content."""
        return """@import "tailwindcss";

/* =============================================================================
   SOURCE FILES
   ============================================================================= */
@source "../../../../.venv/**/djangx/ui/templates/ui/**/*.html";
@source "../../../templates/home/**/*.html";

/* =============================================================================
   THEME CONFIGURATION
   ============================================================================= */
@theme {
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
}

/* =============================================================================
   LIGHT THEME OVERRIDES
   ============================================================================= */
@theme light {
  --color-background: rgba(41, 41, 41, 0.8);
  --color-surface: #484848;
}

/* =============================================================================
   DARK THEME OVERRIDES
   ============================================================================= */
@theme dark {
  --color-background: #060606;
  --color-surface: #252525;
  --color-default: #ffffff;
  --color-heading: #ffffff;
}

/* =============================================================================
   UTILITY CLASSES
   ============================================================================= */
@layer utilities {
  /* Full-width container */
  .container-full {
    @apply mx-auto w-full px-8;
  }

  /* Responsive container (Mobile→SM→MD→LG→XL→2XL: 100%→92%→83%→80%→75%→1400px max) */
  .container {
    @apply mx-auto w-full px-8 sm:w-11/12 sm:px-4 md:w-5/6 lg:w-4/5 xl:w-3/4 xl:px-0 2xl:max-w-[1400px];
  }
}

/* =============================================================================
   BASE STYLES - Global element styling
   ============================================================================= */
@layer base {
  :root {
    @apply scroll-smooth;
  }

  body {
    @apply bg-background text-default font-default antialiased;
  }

  h1,
  h2,
  h3,
  h4,
  h5,
  h6 {
    @apply text-heading font-heading text-balance;
  }

  a {
    @apply text-accent no-underline transition-colors duration-200 ease-in-out;
  }

  a:hover {
    color: color-mix(in srgb, var(--color-accent), white 15%);
  }
}
"""


# ============================================================================
# File Generators
# ============================================================================


class _ProjectFileWriter:
    """Handles file writing operations for project initialization."""

    def __init__(self, project_dir: Path):
        """Initialize the file writer.

        Args:
            project_dir: The project directory path.
        """
        self.project_dir = project_dir

    def write(self, filename: str, content: str) -> None:
        """Write content to a file.

        Args:
            filename: Name of the file to create.
            content: Content to write.

        Raises:
            IOError: If file cannot be written.
            PermissionError: If lacking permission to write.
        """
        file_path = self.project_dir / filename
        file_path.write_text(content.strip(), encoding="utf-8")

    def write_to_path(self, path: Path, content: str) -> None:
        """Write content to a specific path.

        Args:
            path: Full path to the file.
            content: Content to write.

        Raises:
            IOError: If file cannot be written.
            PermissionError: If lacking permission to write.
        """
        path.write_text(content.strip(), encoding="utf-8")

    def ensure_dir(self, path: Path) -> None:
        """Ensure a directory exists.

        Args:
            path: Directory path to create.
        """
        path.mkdir(parents=True, exist_ok=True)


class _HomeAppCreator:
    """Creates the default 'home' Django application."""

    def __init__(self, project_dir: Path, writer: _ProjectFileWriter, templates: _TemplateManager):
        """Initialize the home app creator.

        Args:
            project_dir: The project directory path.
            writer: File writer instance.
            templates: Template manager instance.
        """
        self.project_dir = project_dir
        self.writer = writer
        self.templates = templates
        self.home_dir = project_dir / "home"

    def create(self) -> None:
        """Create the home app with all necessary files and directories."""
        from django.core.management import call_command

        # Create the Django app structure
        call_command("startapp", "home")

        # Create app files
        self._create_urls()
        self._create_views()
        self._create_templates()
        self._create_static_files()

    def _create_urls(self) -> None:
        """Create urls.py for the home app."""
        urls_path = self.home_dir / "urls.py"
        self.writer.write_to_path(urls_path, self.templates.home_urls())

    def _create_views(self) -> None:
        """Create views.py for the home app."""
        views_path = self.home_dir / "views.py"
        self.writer.write_to_path(views_path, self.templates.home_views())

    def _create_templates(self) -> None:
        """Create template directory structure and files."""
        templates_dir = self.home_dir / "templates" / "home"
        self.writer.ensure_dir(templates_dir)

        index_path = templates_dir / "index.html"
        self.writer.write_to_path(index_path, "")

    def _create_static_files(self) -> None:
        """Create static directory structure and CSS files."""
        static_dir = self.home_dir / "static" / "home" / "css"
        self.writer.ensure_dir(static_dir)

        css_path = static_dir / "tailwind.css"
        self.writer.write_to_path(css_path, self.templates.tailwind_css())


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
    ):
        """Initialize the project initializer.

        Args:
            project_dir: The directory where the project will be created.
            dependencies: Dependency manager (uses default if None).
            templates: Template manager (uses default if None).
        """
        self.project_dir = Path(project_dir)
        self.dependencies = dependencies or _ProjectDependencies()
        self.templates = templates or _TemplateManager()
        self.writer = _ProjectFileWriter(self.project_dir)

    def _validate_directory(self) -> None:
        """Validate that the directory is suitable for initialization.

        Raises:
            ProjectInitializationError: If directory is not empty.
        """
        if any(self.project_dir.iterdir()):
            raise ProjectInitializationError(
                f"Directory is not empty. Please choose an empty directory to start a new {PKG_DISPLAY_NAME} project."
            )

    def _get_preset_choice(self, preset: str | None = None) -> PresetType:
        """Get the user's preset choice or validate the provided one.

        Args:
            preset: Optional preset to use without prompting.

        Returns:
            The chosen preset type.

        Raises:
            ValueError: If preset is invalid.
        """
        from rich.prompt import Prompt

        if preset:
            try:
                return PresetType(preset)
            except ValueError:
                valid_presets = [p.value for p in PresetType]
                raise ValueError(
                    f"Invalid preset '{preset}'. Must be one of: {', '.join(valid_presets)}"
                )

        choice = Prompt.ask(
            "Choose a preset",
            choices=[p.value for p in PresetType],
            default=PresetType.DEFAULT.value,
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

        self.writer.write("pyproject.toml", self.templates.pyproject_toml(preset, dependencies))
        self.writer.write(".gitignore", self.templates.gitignore())
        self.writer.write("README.md", self.templates.readme())

    def _configure_preset_files(self, preset: PresetType) -> None:
        """Configure files based on the chosen preset.

        Args:
            preset: The preset configuration to apply.
        """
        if preset == PresetType.VERCEL:
            # Import here to avoid circular dependencies
            from .generators import ServerFileGenerator, VercelFileGenerator

            VercelFileGenerator().create()
            ServerFileGenerator().create()

    def _create_home_app(self) -> None:
        """Create the default home application."""
        home_creator = _HomeAppCreator(self.project_dir, self.writer, self.templates)
        home_creator.create()

    def create(self, preset: str | None = None) -> ExitCode:
        """Execute the full project initialization workflow.

        Args:
            preset: Optional preset to use without prompting.

        Returns:
            ExitCode indicating success or failure.
        """
        from christianwhocodes.io import Text, print

        try:
            # Validate directory is empty
            self._validate_directory()

            # Get and validate preset choice
            chosen_preset = self._get_preset_choice(preset)

            # Create core configuration files
            self._create_core_files(chosen_preset)

            # Configure preset-specific files
            self._configure_preset_files(chosen_preset)

            # Create default app
            self._create_home_app()

            print(
                f"✓ {PKG_DISPLAY_NAME} project initialized successfully!",
                Text.SUCCESS,
            )
            return ExitCode.SUCCESS

        except KeyboardInterrupt:
            print("\nProject initialization cancelled.", Text.WARNING)
            return ExitCode.ERROR

        except ProjectInitializationError as e:
            print(str(e), Text.WARNING)
            return ExitCode.ERROR

        except ValueError as e:
            print(f"Configuration error: {e}", Text.ERROR)
            return ExitCode.ERROR

        except (IOError, PermissionError) as e:
            print(f"File system error: {e}", Text.ERROR)
            return ExitCode.ERROR

        except Exception as e:
            print(f"Unexpected error during initialization: {e}", Text.ERROR)
            return ExitCode.ERROR


# ============================================================================
# Public API
# ============================================================================


def initialize(preset: str | None = None) -> ExitCode:
    """Main entry point for project initialization.

    Args:
        preset: Optional preset to use without prompting.

    Returns:
        ExitCode indicating success or failure.
    """
    return _ProjectInitializer(PROJECT_DIR).create(preset=preset)
