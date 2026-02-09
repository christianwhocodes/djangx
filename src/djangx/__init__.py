from dataclasses import dataclass  # noqa: D104
from pathlib import Path
from typing import Final

__all__: list[str] = [
    "PACKAGE",
    "PROJECT",
]


@dataclass(frozen=True)
class _PackageInfo:
    """Immutable dataclass for package configuration.

    Use when you need to pass package metadata as an instance object,
    for dependency injection, or when working with multiple packages.

    Usage:
        # Create with defaults
        pkg = _PackageInfo.create()
        print(pkg.display_name)

        # Create with custom values
        custom_pkg = _PackageInfo(
            base_dir=Path("/custom/path"),
            name="custom",
            display_name="Custom Package"
        )

        # Pass to functions
        def setup_package(pkg: _PackageInfo) -> None:
            print(f"Setting up {pkg.display_name} at {pkg.base_dir}")
    """

    version: Final[str]
    """The package version, retrieved from metadata."""

    base_dir: Final[Path]
    """The root directory of the package."""

    main_app_dir: Final[Path]
    """Path to the `app` application directory."""

    name: Final[str]
    """The package name (derived from base_dir)."""

    display_name: Final[str]
    """Human-readable display name for the package."""

    main_app_name: Final[str]
    """Name of the `app` application."""

    @classmethod
    def create(cls) -> "_PackageInfo":
        """Create _PackageInfo with default package values.

        Returns:
            _PackageInfo instance configured for the current package.

        """
        from christianwhocodes import Version

        base_dir = Path(__file__).parent.resolve()
        name = base_dir.name
        main_app_dir = base_dir / "app"
        return cls(
            version=Version.get(name)[0],
            base_dir=base_dir,
            main_app_dir=main_app_dir,
            name=name,  # djangx
            display_name=name[0].upper() + name[1:-1] + name[-1].upper(),  # DjangX
            main_app_name=main_app_dir.name,  # app
        )


PACKAGE = _PackageInfo.create()
"""Default package configuration instance."""


@dataclass(frozen=True)
class _ProjectInfo:
    """Immutable dataclass for project configuration.

    Use when you need to pass project paths/config as an instance object,
    for dependency injection, testing with different paths, or managing
    multiple project configurations.

    Usage:
        # Create with defaults (current working directory)
        project = _ProjectInfo.create()
        print(project.name)
        print(project.home_app_dir)

        # Create with custom paths for testing
        test_project = _ProjectInfo(
            base_dir=Path("/tmp/test"),
            home_app_dir=Path("/tmp/test/home"),
            public_dir=Path("/tmp/test/public"),
            api_dir=Path("/tmp/test/api"),
            init_name="test_project",
            home_app_name="home"
        )

        # Pass to functions
        def init_project(project: _ProjectInfo) -> None:
            project.home_app_dir.mkdir(parents=True, exist_ok=True)
            project.public_dir.mkdir(parents=True, exist_ok=True)
    """

    base_dir: Final[Path]
    """The root directory of the project."""

    home_app_dir: Final[Path]
    """Path to the `home` application directory."""

    home_app_exists: Final[bool]
    """Whether the `home` application directory exists."""

    public_dir: Final[Path]
    """Path to the public/static files directory."""

    api_dir: Final[Path]
    """Path to the API application directory."""

    init_name: Final[str]
    """The base directory name."""

    home_app_name: Final[str]
    """Name of the home application."""

    @classmethod
    def create(cls) -> "_ProjectInfo":
        """Create _ProjectInfo with default values based on current working directory.

        Returns:
            _ProjectInfo instance configured for the current project.

        """
        base_dir = Path.cwd()
        return cls(
            base_dir=base_dir,
            home_app_dir=base_dir / "home",
            home_app_exists=(base_dir / "home").exists() and (base_dir / "home").is_dir(),
            public_dir=base_dir / "public",
            api_dir=base_dir / "api",
            init_name=base_dir.name,
            home_app_name="home",
        )


PROJECT = _ProjectInfo.create()
"""Default project configuration instance based on current working directory."""
