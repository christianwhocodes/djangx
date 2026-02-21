"""Configuration field descriptors and base settings class."""

import builtins
import pathlib
from typing import Any, TypeAlias, cast

from ... import PROJECT

__all__: list[str] = [
    "SettingConf",
    "ConfField",
]

_ConfDefaultValueType: TypeAlias = str | bool | list[str] | pathlib.Path | int | None


class ConfField:
    """Descriptor for a configuration field populated from env vars or TOML."""

    def __init__(
        self,
        type: type[str] | type[bool] | type[list[str]] | type[pathlib.Path] | type[int] = str,
        choices: list[str] | None = None,
        env: str | None = None,
        toml: str | None = None,
        default: _ConfDefaultValueType = None,
    ):
        """Set up field type, source mappings, and default value."""
        self.type = type
        self.choices = choices
        self.env = env
        self.toml = toml
        self.default = default

    @property
    def as_dict(self) -> dict[str, Any]:
        """Dictionary representation of the field."""
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
    def convert_value(
        value: Any, target_type: Any, field_name: str | None = None
    ) -> _ConfDefaultValueType:
        """Convert a raw value to the target type."""
        from christianwhocodes import TypeConverter

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
        """Get descriptor value (should be converted to property)."""
        if instance is None:
            return self
        raise AttributeError(f"{self.__class__.__name__} should have been converted to a property")


class SettingConf:
    """Base class for loading settings from env vars and TOML."""

    # Track all Conf subclasses
    _subclasses: list[type["SettingConf"]] = []

    def _get_from_toml(self, key: str | None) -> Any:
        """Get value from TOML configuration."""
        if key is None:
            return None

        current: Any = PROJECT.toml
        for k in key.split("."):
            if isinstance(current, dict) and k in current:
                current = cast(Any, current[k])
            else:
                return None

        return current

    def _fetch_value(
        self,
        env_key: str | None = None,
        toml_key: str | None = None,
        default: _ConfDefaultValueType = None,
    ) -> Any:
        """Fetch configuration value with fallback priority: ENV -> TOML -> default."""
        # Try environment variable first
        if env_key is not None and env_key in PROJECT.env:
            return PROJECT.env[env_key]

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
        """Convert ConfField descriptors to properties on subclass creation."""
        super().__init_subclass__()

        # Register this subclass
        SettingConf._subclasses.append(cls)

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
                def getter(self: "SettingConf") -> Any:
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
        """Collect all ConfField definitions that use environment variables."""
        env_fields: list[dict[str, Any]] = []

        for subclass in cls._subclasses:
            if hasattr(subclass, "_env_fields"):
                env_fields.extend(subclass._env_fields)

        return env_fields
