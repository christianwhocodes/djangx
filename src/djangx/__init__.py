import builtins
import pathlib
import sys
from os import environ
from typing import Any, NoReturn, Optional, TypeAlias, cast

from christianwhocodes.core import ExitCode, PyProject, TypeConverter
from christianwhocodes.io import Text, print
from dotenv import dotenv_values

# Directories

PKG_DIR: pathlib.Path = pathlib.Path(__file__).parent.resolve()

PKG_UI_DIR: pathlib.Path = PKG_DIR / "ui"

PKG_API_DIR: pathlib.Path = PKG_DIR / "api"

PKG_MANAGEMENT_DIR: pathlib.Path = PKG_DIR / "management"

PROJECT_DIR: pathlib.Path = pathlib.Path.cwd()

PROJECT_MAIN_APP_DIR: pathlib.Path = PROJECT_DIR / "home"

PROJECT_PUBLIC_DIR: pathlib.Path = PROJECT_DIR / "public"

PROJECT_API_DIR: pathlib.Path = PROJECT_DIR / "api"


# Names

PKG_NAME: str = PKG_DIR.name

PKG_DISPLAY_NAME: str = "DjangX"

PKG_UI_NAME: str = "ui"

PKG_API_NAME: str = "api"

PKG_MANAGEMENT_NAME: str = "management"

PROJECT_MAIN_APP_NAME: str = "home"

# Settings configuration classes

_ValueType: TypeAlias = Optional[str | bool | list[str] | pathlib.Path | int]


class ConfField:
    """
    Configuration field descriptor.

    This class defines a configuration field that can be populated from either
    environment variables or TOML configuration files.

    Args:
        env: Environment variable name to read from
        toml: TOML key path (dot-separated) to read from
        default: Default value if not found in env or TOML
        type: Type to convert the value to. Supports:
            - str, bool, pathlib.Path
            - list[str] for list of strings
    """

    def __init__(
        self,
        type: type[str] | type[bool] | type[list[str]] | type[pathlib.Path] | type[int] = str,
        choices: Optional[list[str]] = None,
        env: Optional[str] = None,
        toml: Optional[str] = None,
        default: _ValueType = None,
    ):
        self.type = type
        self.choices = choices
        self.env = env
        self.toml = toml
        self.default = default

    @property
    def as_dict(self) -> dict[str, Any]:
        """
        Convert the ConfField to a dictionary representation.

        Returns:
            Dictionary containing all field configuration
        """
        return {
            "env": self.env,
            "toml": self.toml,
            "default": self.default,
            "type": self.type,
        }

    # ============================================================================
    # Value Conversion
    # ============================================================================

    @staticmethod
    def convert_value(value: Any, target_type: Any, field_name: Optional[str] = None) -> _ValueType:
        """
        Convert the raw value to the appropriate type.

        Args:
            value: Raw value from env or TOML
            target_type: The type to convert to
            field_name: Name of the field (for error messages)

        Returns:
            Converted value of the appropriate type

        Raises:
            ValueError: If conversion fails
        """
        if value is None:
            match target_type:
                case builtins.str:
                    return ""
                case builtins.int:
                    return 0
                case builtins.list:
                    return []
                case _:
                    return None

        try:
            match target_type:
                case builtins.str:
                    return str(value)
                case builtins.int:
                    return int(value)
                case builtins.list:
                    return TypeConverter.to_list_of_str(value, str.strip)
                case builtins.bool:
                    return TypeConverter.to_bool(value)
                case pathlib.Path:
                    return TypeConverter.to_path(value)
                case _:
                    raise ValueError(f"Unsupported target type or type not specified: {target_type}")

        except ValueError as e:
            field_info = f" for field '{field_name}'" if field_name else ""
            raise ValueError(f"Error converting config value{field_info}: {e}") from e

    # ============================================================================
    # Descriptor Protocol
    # ============================================================================

    def __get__(self, instance: Any, owner: type) -> Any:
        """
        This shouldn't be called since BaseConfig converts these to properties.
        """
        if instance is None:
            return self
        raise AttributeError(f"{self.__class__.__name__} should have been converted to a property")


class Conf:
    """Base configuration class that handles loading from environment variables and TOML files."""

    # Track all Conf subclasses
    _subclasses: list[type["Conf"]] = []

    # ============================================================================
    # Configuration Loading
    # ============================================================================
    _toml_section: Optional[dict[str, Any]] = None
    _validated: bool = False

    def __init__(self):
        """Initialize and validate project on first instantiation."""
        if not self._validated:
            self._load_project()

    @classmethod
    def _check_pyproject_toml(cls) -> dict[str, Any]:
        f"""
        Validate and extract 'tool.{PKG_NAME}' configuration from 'pyproject.toml'.

        Returns:
            The 'tool.{PKG_NAME}' configuration section from 'pyproject.toml'

        Raises:
            FileNotFoundError: If 'pyproject.toml' doesn't exist
            KeyError: If 'tool.{PKG_NAME}' section is missing
        """
        pyproject_path = PROJECT_DIR / "pyproject.toml"

        if not pyproject_path.exists():
            raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

        tool_section = PyProject(pyproject_path).data.get("tool", {})

        if PKG_NAME in tool_section:
            return tool_section[PKG_NAME]
        else:
            raise KeyError(f"Missing 'tool.{PKG_NAME}' section in pyproject.toml")

    @classmethod
    def _load_project(cls) -> Optional[NoReturn]:
        """Load and validate project configuration."""
        try:
            # ?: Should other project indicators be added?
            toml_section = cls._check_pyproject_toml()

        except (FileNotFoundError, KeyError, ValueError) as e:
            cls._validated = False
            print(
                f"Are you currently executing in a {PKG_DISPLAY_NAME} project base directory?\n"
                f"If not, navigate to your project's root or create a new {PKG_DISPLAY_NAME} project to run the command.\n\n"
                "A valid project requires:\n"
                f"  - `pyproject.toml` file with a 'tool.{PKG_NAME}' section (even if empty)\n"
                f"Validation failed: {e}",
                Text.WARNING,
            )

        except Exception as e:
            cls._validated = False
            print(
                f"Unexpected error during project validation:\n{e}",
                Text.WARNING,
            )

        else:
            # Success - store configuration
            cls._validated = True
            cls._toml_section = toml_section

        finally:
            if not cls._validated:
                sys.exit(ExitCode.ERROR)

    @property
    def _env(self) -> dict[str, Any]:
        """Get combined .env and environment variables as a dictionary."""
        if not self._validated:
            self._load_project()
        return {
            **dotenv_values(PROJECT_DIR / ".env"),
            **environ,  # override loaded values with environment variables
        }

    @property
    def _toml(self) -> dict[str, Any]:
        """Get TOML configuration section."""
        if not self._validated:
            self._load_project()
        assert self._toml_section is not None
        return self._toml_section

    def _get_from_toml(self, key: Optional[str]) -> Any:
        """Get value from TOML configuration."""
        if key is None:
            return None

        current: Any = self._toml
        for k in key.split("."):
            if isinstance(current, dict) and k in current:
                current = cast(Any, current[k])
            else:
                return None

        return current

    def _fetch_value(
        self,
        env_key: Optional[str] = None,
        toml_key: Optional[str] = None,
        default: _ValueType = None,
    ) -> Any:
        """
        Fetch configuration value with fallback priority: ENV -> TOML -> default.
        """
        # Try environment variable first
        if env_key is not None and env_key in self._env:
            return self._env[env_key]

        # Fall back to TOML config
        toml_value = self._get_from_toml(toml_key)
        if toml_value is not None:
            return toml_value

        # Final fallback to default
        return default

    # ============================================================================
    # Class Setup
    # ============================================================================

    def __init_subclass__(cls) -> None:
        """
        Automatically convert ConfField descriptors to properties
        when a subclass is created.
        """
        super().__init_subclass__()

        # Register this subclass
        Conf._subclasses.append(cls)

        # Initialize _env_fields for this subclass
        if not hasattr(cls, "_env_fields"):
            cls._env_fields: list[dict[str, Any]] = []

        for attr_name, attr_value in list(vars(cls).items()):
            # Skip private attributes, methods, and special descriptors
            if (
                attr_name.startswith("_")
                or callable(attr_value)
                or isinstance(attr_value, (classmethod, staticmethod, property))
            ):
                continue

            # Check if this is a ConfField
            if not isinstance(attr_value, ConfField):
                continue

            # Store field metadata if it has an env key
            if attr_value.env is not None:
                cls._env_fields.append(
                    {
                        "class": cls.__name__,
                        "choices": attr_value.choices,
                        "env": attr_value.env,
                        "toml": attr_value.toml,
                        "default": attr_value.default,
                        "type": attr_value.type,
                    }
                )

            # Create property getter with captured config
            def make_getter(field_name: str, field_config: dict[str, Any]):
                def getter(self: "Conf") -> Any:
                    raw_value = self._fetch_value(
                        field_config["env"], field_config["toml"], field_config["default"]
                    )
                    return ConfField.convert_value(raw_value, field_config["type"], field_name)

                return getter

            setattr(
                cls,
                attr_name,
                property(make_getter(attr_name, attr_value.as_dict)),
            )

    # ============================================================================
    # Metadata
    # ============================================================================

    @classmethod
    def get_env_fields(cls) -> list[dict[str, Any]]:
        """
        Collect all ConfField definitions that use environment variables
        from all Conf subclasses.

        Returns:
            List of dicts containing class, env key, toml key, choices key, default key and type key for each field
        """
        env_fields: list[dict[str, Any]] = []

        for subclass in cls._subclasses:
            if hasattr(subclass, "_env_fields"):
                env_fields.extend(subclass._env_fields)

        return env_fields
