"""Project initialization command."""

from argparse import ArgumentParser, Namespace
from pathlib import Path

from christianwhocodes import (
    BaseCommand,
    ExitCode,
    FileGenerator,
    FileSpec,
    InitAction,
    PostgresFilename,
    Text,
    cprint,
)

from ... import PACKAGE, PROJECT
from ..enums import DatabaseEnum, PresetEnum

__all__: list[str] = ["StartprojectCommand"]


class _PresetDatabaseIncompatibilityError(Exception):
    """Raised when a preset is used with an incompatible database."""


class StartprojectCommand(BaseCommand):
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
            choices=[p for p in PresetEnum],
            help="Project preset to use.",
            default=PresetEnum.DEFAULT,
        )
        parser.add_argument(
            "--db",
            type=DatabaseEnum,
            choices=[db for db in DatabaseEnum],
            help="Database backend to use.",
        )
        pg_config_group = parser.add_mutually_exclusive_group()
        pg_config_group.add_argument(
            "--pg-use-env-vars",
            action="store_true",
            help="Use environment variables for PostgreSQL configuration.",
        )
        pg_config_group.add_argument(
            "--pg-use-service-files",
            action="store_true",
            help=f"Use a `{PostgresFilename.PGSERVICE}` and `{PostgresFilename.PGPASS}` file for PostgreSQL configuration.",
        )

    def handle(self, args: Namespace) -> ExitCode:
        """Execute the command logic with the parsed arguments."""
        try:
            self._project_dir = Path.cwd() / args.project_name
            self._validated_args = self._validate_args(args)
            self._validate_project_directory(self._project_dir, self._validated_args)
            self._generate_files(self._project_dir, self._validated_args)

        except (_PresetDatabaseIncompatibilityError, FileExistsError) as e:
            cprint(str(e), Text.ERROR)
            return ExitCode.ERROR

        except Exception as e:
            cprint(f"An unexpected error occurred: {e}", Text.ERROR)
            self._revert_generated_files(self._project_dir)
            return ExitCode.ERROR

        else:
            return ExitCode.SUCCESS

    def _validate_args(self, args: Namespace) -> Namespace:
        """Validate the provided arguments."""
        match args.preset:
            case PresetEnum.VERCEL:
                if args.db == DatabaseEnum.SQLITE3:
                    raise _PresetDatabaseIncompatibilityError(
                        f"Error: The {PresetEnum.VERCEL} preset requires {DatabaseEnum.POSTGRESQL}. "
                        f"You cannot use {args.db} with this preset."
                    )
                args.db = DatabaseEnum.POSTGRESQL

            case _:
                if not args.db:
                    args.db = DatabaseEnum.SQLITE3

        if args.db == DatabaseEnum.POSTGRESQL and not (
            args.pg_use_env_vars or args.pg_use_service_files
        ):
            args.pg_use_env_vars = True

        return args

    def _validate_project_directory(self, project_dir: Path, args: Namespace) -> None:
        """Check if the project directory already exists and is not empty."""
        if args.project_name == "." and any(project_dir.iterdir()):
            raise FileExistsError(
                "The current directory is not empty. Please choose a different project name or remove the existing files."
            )
        elif project_dir.exists() and project_dir.is_file():
            raise FileExistsError(
                f"A file named '{project_dir}' already exists. Please choose a different project name or remove the existing file."
            )
        elif project_dir.exists() and any(project_dir.iterdir()):
            raise FileExistsError(
                f"The directory '{project_dir}' already exists and is not empty. Please choose a different project name or remove the existing files in the directory."
            )

    def _generate_files(self, project_dir: Path, args: Namespace) -> None:
        """Generate other necessary files."""
        home_app_dir: Path = project_dir / "home"

        files_with_content: list[tuple[Path, str]] = [
            (project_dir / "pyproject.toml", self._get_pyproject_toml_content(args)),
            (home_app_dir / "apps.py", self._get_home_app_apps_py_content()),
            (home_app_dir / "views.py", self._get_home_app_views_py_content()),
            (home_app_dir / "urls.py", self._get_home_app_urls_py_content()),
            (home_app_dir / "admin.py", self._get_home_app_admin_py_content()),
            (home_app_dir / "models.py", self._get_home_app_models_py_content()),
            (home_app_dir / "tests.py", self._get_home_app_tests_py_content()),
            (
                home_app_dir / "templates" / PROJECT.home_app_name / "index.html",
                self._get_home_app_index_html_content(),
            ),
        ]

        for path, content in files_with_content:
            FileGenerator(FileSpec(path=path, content=content)).create()

        for file in [
            home_app_dir / "__init__.py",
            home_app_dir / "migrations" / "__init__.py",
            project_dir / "README.md",
        ]:
            file.parent.mkdir(parents=True, exist_ok=True)
            file.touch(exist_ok=True)

    def _revert_generated_files(self, project_dir: Path) -> None:
        """Remove any files that were generated before an error occurred."""
        if project_dir.exists():
            for item in sorted(project_dir.rglob("*"), reverse=True):
                item.unlink() if item.is_file() else item.rmdir()

    def _get_pyproject_toml_content(self, args: Namespace) -> str:
        """Generate the content for pyproject.toml based on the provided arguments."""
        return "trial pyproject content"

    def _get_home_app_apps_py_content(self) -> str:
        """Generate the content for the home app apps.py."""
        return (
            "from django.apps import AppConfig\n\n\n"
            "class HomeConfig(AppConfig):\n"
            '    name = "home"\n'
        )

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
