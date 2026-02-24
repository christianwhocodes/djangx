"""Project initialization command."""

from argparse import ArgumentParser, Namespace
from pathlib import Path

from christianwhocodes import BaseCommand, ExitCode, FileGenerator, FileSpec, InitAction, PostgresFilename, Text, cprint, status

from ... import PACKAGE, PROJECT
from ..enums import DatabaseEnum, PostgresFlagEnum, PresetEnum, StorageEnum


class Command(BaseCommand):
    """Command to initialize a new project."""

    _project_dir: Path
    _validated_args: Namespace
    _actions = " | ".join(InitAction)
    prog = f"{PACKAGE.name} [{_actions}] <project_name>"
    help = f"Initialize a new {PACKAGE.display_name} project."

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Register arguments onto the parser."""
        parser.add_argument("project_name", help="Name of the project to initialize.")
        parser.add_argument(
            "-p",
            "--preset",
            dest="preset",
            type=PresetEnum,
            choices=[p.value for p in PresetEnum],
            help="Project preset to use. Defaults to the 'default' preset.",
            default=PresetEnum.DEFAULT,
        )
        parser.add_argument(
            "-d",
            "--db",
            dest="db",
            type=DatabaseEnum,
            choices=[db.value for db in DatabaseEnum],
            help="Database backend to use.",
        )
        parser.add_argument(
            PostgresFlagEnum.USE_ENV_VARS.value,
            action="store_true",
            help=f"Use environment variables for PostgreSQL configuration. If False, configuration will be read from {PostgresFilename.PGSERVICE} and {PostgresFilename.PGPASS} files.",
        )
        parser.add_argument(
            "--disable-tailwindcss",
            action="store_true",
            help="Disable TailwindCSS in the generated project.",
        )

    def handle(self, args: Namespace) -> ExitCode:
        """Execute the command logic with the parsed arguments."""
        try:
            self._project_dir = Path.cwd() / args.project_name
            self._validated_args = self._validate_args(args)
            self._validate_project_directory(self._project_dir, self._validated_args)

            with status("Generating base project files..."):
                self._generate_base_files(self._project_dir, self._validated_args)
            with status("Generating preset files..."):
                self._generate_preset_files(self._project_dir, self._validated_args)

        except (ValueError, FileExistsError) as e:
            cprint(str(e), Text.ERROR)
            return ExitCode.ERROR

        except Exception as e:
            cprint(f"Error occurred during project initialization:\n{e}", Text.ERROR)
            self._revert_generated_files(self._project_dir)
            return ExitCode.ERROR

        else:
            self._display_successful_setup_info(self._project_dir)
            return ExitCode.SUCCESS

    def _validate_args(self, args: Namespace) -> Namespace:
        """Validate the provided arguments."""
        match args.preset:
            case PresetEnum.VERCEL:
                """Enforce postgresql and environment variable configuration for Vercel preset due to platform requirements and security best practices."""
                if args.db == DatabaseEnum.SQLITE3:
                    raise ValueError(f"The {PresetEnum.VERCEL.value} preset requires {DatabaseEnum.POSTGRESQL.value}.")

                args.db = DatabaseEnum.POSTGRESQL
                args.pg_use_env_vars = True

            case _:
                """Other presets work with either database. Default to sqlite3 if args.db is unspecified."""
                if not args.db:
                    args.db = DatabaseEnum.SQLITE3

        if args.pg_use_env_vars and not args.db == DatabaseEnum.POSTGRESQL:
            raise ValueError(
                f"The {PostgresFlagEnum.USE_ENV_VARS.value} flag is only supported for {DatabaseEnum.POSTGRESQL.value}."
            )

        return args

    def _validate_project_directory(self, project_dir: Path, args: Namespace) -> None:
        """Check if the project directory already exists and is not empty."""
        if args.project_name == "." and any(project_dir.iterdir()):
            raise FileExistsError(
                "The current directory is not empty. Please choose a different project name or remove the existing files."
            )

        if not project_dir.exists():
            return

        if project_dir.is_file():
            raise FileExistsError(
                f"A file named '{project_dir}' already exists. Please choose a different project name or remove the existing file."
            )

        if any(project_dir.iterdir()):
            raise FileExistsError(
                f"The directory '{project_dir}' already exists and is not empty. Please choose a different project name or remove the existing files in the directory."
            )

    def _generate_base_files(self, project_dir: Path, args: Namespace) -> None:
        """Generate base project files."""
        home_app_dir: Path = project_dir / "home"

        files_with_content: list[tuple[Path, str]] = [
            (project_dir / "pyproject.toml", self._get_pyproject_toml_content(project_dir, args)),
            (project_dir / ".gitignore", self._get_gitignore_content(args)),
            (project_dir / "README.md", self._get_readme_content(project_dir)),
            (home_app_dir / "__init__.py", ""),
            (home_app_dir / "migrations" / "__init__.py", ""),
            (home_app_dir / "templates" / PROJECT.home_app_name / "index.html", self._get_home_app_index_html_content()),
            (home_app_dir / "apps.py", self._get_home_app_apps_py_content()),
            (home_app_dir / "views.py", self._get_home_app_views_py_content()),
            (home_app_dir / "urls.py", self._get_home_app_urls_py_content()),
            (home_app_dir / "admin.py", self._get_home_app_admin_py_content()),
            (home_app_dir / "models.py", self._get_home_app_models_py_content()),
            (home_app_dir / "tests.py", self._get_home_app_tests_py_content()),
            *(
                [
                    (
                        home_app_dir / "static" / PROJECT.home_app_name / "css" / "source.css",
                        self._get_home_app_tailwindcss_content(),
                    )
                ]
                if not args.disable_tailwindcss
                else []
            ),
        ]

        for path, content in files_with_content:
            FileGenerator(FileSpec(path=path, content=content)).create()

    def _generate_preset_files(self, project_dir: Path, args: Namespace) -> None:
        """Generate preset-specific files."""
        from .generate import get_api_server_spec, get_env_spec, get_vercel_spec

        match args.preset:
            case PresetEnum.VERCEL:
                api_dir: Path = project_dir / "api"
                FileGenerator(get_vercel_spec(path=project_dir / "vercel.json")).create()
                FileGenerator(get_api_server_spec(path=api_dir / "server.py")).create()
                FileGenerator(FileSpec(path=api_dir / "__init__.py", content="")).create()
            case _:
                pass
        FileGenerator(get_env_spec(path=project_dir / ".env.example")).create()

    def _revert_generated_files(self, project_dir: Path) -> None:
        """Remove any files that were generated before an error occurred."""
        if project_dir.exists():
            for item in sorted(project_dir.rglob("*"), reverse=True):
                item.unlink() if item.is_file() else item.rmdir()

    def _get_pyproject_toml_content(self, project_dir: Path, args: Namespace) -> str:
        """Generate the content for pyproject.toml based on the provided arguments."""
        deps = [
            '    "pillow>=12.1.1",',
            f'    "{PACKAGE.name}>=1.5.7",',
        ]
        if args.db == DatabaseEnum.POSTGRESQL:
            deps.insert(1, '    "psycopg[binary,pool]>=3.3.3",')
        if args.preset == PresetEnum.VERCEL:
            deps.append('    "vercel>=0.5.0",')

        dependencies = "\n".join(deps)

        djangx_section = f"[tool.{PACKAGE.name}]\n"
        if args.db == DatabaseEnum.POSTGRESQL:
            djangx_section += f'db = {{ backend = "{DatabaseEnum.POSTGRESQL.value}", use-env-vars = {"true" if args.pg_use_env_vars else "false"} }}\n'
        if args.preset == PresetEnum.VERCEL:
            djangx_section += f'storage = {{ backend = "{StorageEnum.VERCELBLOB.value}", blob-token = "get-from-vercel-blob-storage-and-keep-private-via-env-var" }}\n'
        if args.disable_tailwindcss:
            djangx_section += "tailwindcss = { disabled = true }\n"

        return (
            "[project]\n"
            f'name = "{project_dir.name}"\n'
            'version = "0.1.0"\n'
            'description = ""\n'
            'readme = "README.md"\n'
            'requires-python = ">=3.12"\n'
            "dependencies = [\n"
            f"{dependencies}\n"
            "]\n"
            "\n"
            "[dependency-groups]\n"
            'dev = ["djlint>=1.36.4"]\n'
            "\n"
            f"{djangx_section}"
        )

    def _get_gitignore_content(self, args: Namespace) -> str:
        """Generate the content for .gitignore based on the provided arguments."""
        sqlite_line = "\n# SQLite database file\n/db.sqlite3\n" if args.db == DatabaseEnum.SQLITE3 else ""

        return (
            "# Python-generated files\n"
            "__pycache__/\n"
            "*.py[oc]\n"
            "build/\n"
            "dist/\n"
            "wheels/\n"
            "*.egg-info\n"
            "\n"
            "# Virtual environments\n"
            "/.venv/\n"
            "\n"
            "# Ruff cache\n"
            "/.ruff_cache/\n"
            "\n"
            "# Temporary files\n"
            "/.tmp/\n"
            "\n"
            "# Static and media files\n"
            "/public/\n"
            "\n"
            "# Environment variables files\n"
            "/.env*\n"
            f"{sqlite_line}"
        )

    def _get_home_app_apps_py_content(self) -> str:
        """Generate the content for the home app apps.py."""
        return 'from django.apps import AppConfig\n\n\nclass HomeConfig(AppConfig):\n    name = "home"\n'

    def _get_home_app_views_py_content(self) -> str:
        """Generate the content for the home app views.py."""
        return (
            "from django.views.generic.base import TemplateView\n\n\n"
            "class HomeView(TemplateView):\n"
            '    template_name = "home/index.html"\n'
        )

    def _get_home_app_urls_py_content(self) -> str:
        """Generate the content for the home app urls.py."""
        return (
            "from django.contrib import admin\n"
            "from django.urls import URLPattern, URLResolver, path\n\n"
            "from . import views\n\n"
            "urlpatterns: list[URLPattern | URLResolver] = [\n"
            '    path("admin/", admin.site.urls),\n'
            '    path("", views.HomeView.as_view(), name="home"),\n'
            "]\n"
        )

    def _get_home_app_admin_py_content(self) -> str:
        """Generate the content for the home app admin.py."""
        return "# from django.contrib import admin\n\n# Register your models here.\n"

    def _get_home_app_models_py_content(self) -> str:
        """Generate the content for the home app models.py."""
        return "# from django.db import models\n\n# Create your models here.\n"

    def _get_home_app_tests_py_content(self) -> str:
        """Generate the content for the home app tests.py."""
        return "# from django.test import TestCase\n\n# Create your tests here.\n"

    def _get_home_app_index_html_content(self) -> str:
        """Generate the content for the home app index.html."""
        return (
            '{% extends "base/default.html" %}\n'
            "{% load org %}\n"
            "{% block title %}\n"
            '    <title>Welcome - {% org "name" %} App</title>\n'
            "{% endblock title %}\n"
            "{% block fonts %}\n"
            '    <link href="https://fonts.googleapis.com" rel="preconnect" />\n'
            '    <link href="https://fonts.gstatic.com" rel="preconnect" crossorigin />\n'
            '    <link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100;0,300;0,400;0,500;0,700;0,900;1,100;1,300;1,400;1,500;1,700;1,900&family=Raleway:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&family=Mulish:ital,wght@0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap"\n'
            '          rel="stylesheet" />\n'
            "{% endblock fonts %}\n"
            "{% block main %}\n"
            "    <main>\n"
            '        <section class="container-full py-8">\n'
            '            <p class="text-accent">Welcome to the {% org "name" %} App!</p>\n'
            "        </section>\n"
            "    </main>\n"
            "{% endblock main %}\n"
        )

    def _get_home_app_tailwindcss_content(self) -> str:
        """Generate the content for the home app tailwind.css."""
        return (
            '@import "tailwindcss";\n'
            "\n"
            "/* =============================================================================\n"
            "   SOURCE FILES\n"
            "   ============================================================================= */\n"
            f'@source "../../../../.venv/**/{PACKAGE.name}/{PACKAGE.main_app_name}/templates/{PACKAGE.main_app_name}/**/*.html";\n'
            f'@source "../../../templates/{PROJECT.home_app_name}/**/*.html";\n'
            "\n"
            "/* =============================================================================\n"
            "   THEME CONFIGURATION\n"
            "   ============================================================================= */\n"
            "@theme {\n"
            "  /* ---------------------------------------------------------------------------\n"
            "     TYPOGRAPHY\n"
            "     --------------------------------------------------------------------------- */\n"
            "  /* Default body text font */\n"
            "  --font-default:\n"
            '    "Roboto", system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue",\n'
            '    Arial, "Noto Sans", "Liberation Sans", sans-serif, "Apple Color Emoji",\n'
            '    "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";\n'
            "  /* Headings font family */\n"
            '  --font-heading: "Mulish", system-ui, -apple-system, sans-serif;\n'
            "  /* Navigation font family */\n"
            '  --font-nav: "Raleway", system-ui, -apple-system, sans-serif;\n'
            "\n"
            "  /* ---------------------------------------------------------------------------\n"
            "     COLOR PALETTE - Base color system\n"
            "     --------------------------------------------------------------------------- */\n"
            "  /* Accent Colors */\n"
            "  --color-accent: #ff4d4f; /* Primary accent for your brand (links, CTAs) */\n"
            "  /* Background Colors */\n"
            "  --color-background: #141414; /* Main page background */\n"
            "  --color-surface: #1c1c1c; /* Elevated surfaces (cards, panels) */\n"
            "  /* Text Colors */\n"
            "  --color-default: #d9d9d9; /* Default body text */\n"
            "  --color-heading: #ededed; /* Headings and titles */\n"
            "  --color-contrast: #ffffff; /* Contrast text elements, ensuring readability against backgrounds, accent, headings, default colors  */\n"
            "\n"
            "  /* ---------------------------------------------------------------------------\n"
            "     NAVIGATION COLORS - Navigation component tokens\n"
            "     --------------------------------------------------------------------------- */\n"
            "  /* Desktop Navigation */\n"
            "  --color-nav: #d9d9d9; /* Default nav link color */\n"
            "  --color-nav-hover: #ff4d4f; /* Nav link hover state */\n"
            "  /* Mobile Navigation */\n"
            "  --color-nav-mobile-bg: #2e2e2e; /* Mobile menu background */\n"
            "  /* Dropdown Menus */\n"
            "  --color-nav-dropdown-bg: #2e2e2e; /* Dropdown background */\n"
            "  --color-nav-dropdown: #d9d9d9; /* Dropdown text color */\n"
            "  --color-nav-dropdown-hover: #ff4d4f; /* Dropdown hover state */\n"
            "}\n"
            "\n"
            "/* =============================================================================\n"
            "   LIGHT THEME OVERRIDES\n"
            "   ============================================================================= */\n"
            "@theme light {\n"
            "  --color-background: rgba(41, 41, 41, 0.8);\n"
            "  --color-surface: #484848;\n"
            "}\n"
            "\n"
            "/* =============================================================================\n"
            "   DARK THEME OVERRIDES\n"
            "   ============================================================================= */\n"
            "@theme dark {\n"
            "  --color-background: #060606;\n"
            "  --color-surface: #252525;\n"
            "  --color-default: #ffffff;\n"
            "  --color-heading: #ffffff;\n"
            "}\n"
            "\n"
            "/* =============================================================================\n"
            "   UTILITY CLASSES\n"
            "   ============================================================================= */\n"
            "@layer utilities {\n"
            "  /* Full-width container */\n"
            "  .container-full {\n"
            "    @apply mx-auto w-full px-8;\n"
            "  }\n"
            "\n"
            "  /* Responsive container (Mobile→SM→MD→LG→XL→2XL: 100%→92%→83%→80%→75%→1400px max) */\n"
            "  .container {\n"
            "    @apply mx-auto w-full px-8 sm:w-11/12 sm:px-4 md:w-5/6 lg:w-4/5 xl:w-3/4 xl:px-0 2xl:max-w-[1400px];\n"
            "  }\n"
            "}\n"
            "\n"
            "/* =============================================================================\n"
            "   BASE STYLES - Global element styling\n"
            "   ============================================================================= */\n"
            "@layer base {\n"
            "  :root {\n"
            "    @apply scroll-smooth;\n"
            "  }\n"
            "\n"
            "  body {\n"
            "    @apply bg-background text-default font-default antialiased;\n"
            "  }\n"
            "\n"
            "  h1,\n"
            "  h2,\n"
            "  h3,\n"
            "  h4,\n"
            "  h5,\n"
            "  h6 {\n"
            "    @apply text-heading font-heading text-balance;\n"
            "  }\n"
            "\n"
            "  a {\n"
            "    @apply text-accent no-underline transition-colors duration-200 ease-in-out;\n"
            "  }\n"
            "\n"
            "  a:hover {\n"
            "    color: color-mix(in srgb, var(--color-accent), white 15%);\n"
            "  }\n"
            "}\n"
        )

    def _get_readme_content(self, project_dir: Path) -> str:
        """Generate the content for README.md."""
        return f"# {project_dir.name}\n"

    def _display_successful_setup_info(self, project_dir: Path) -> None:
        """Display setup success message."""
        cprint(f"✓ Project '{project_dir.name}' initialized successfully!", Text.SUCCESS)
