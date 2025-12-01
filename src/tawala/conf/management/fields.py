from typing import Any, Dict, Optional

from ...core.management.utils import (
    to_bool,
    to_list_of_str,
    to_str_if_value_else_empty_str,
)


class BaseConfField:
    """
    Base class for configuration field descriptors.
    Handles common type conversion logic.
    """

    # Define which fields need special type handling
    BOOL_FIELDS = {"debug", "use_vars", "pool"}
    LIST_FIELDS = {"allowed_hosts", "configured_apps", "commands"}

    def __init__(self):
        self.name: Optional[str] = None

    def __set_name__(self, owner: type, name: str) -> None:
        """Store the attribute name for type conversion."""
        self.name = name

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the field to a dictionary format expected by BaseConfig.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement to_dict()")

    def convert_value(self, value: Any) -> Any:
        """
        Convert the raw value to the appropriate type based on field name.

        Args:
            value: Raw value from env or TOML

        Returns:
            Converted value of the appropriate type
        """
        # Handle None values with sensible defaults
        if value is None:
            if self.name in self.BOOL_FIELDS:
                return False
            if self.name in self.LIST_FIELDS:
                return []
            return ""

        # Handle boolean fields
        if self.name in self.BOOL_FIELDS:
            return to_bool(value)

        # Handle list fields
        if self.name in self.LIST_FIELDS:
            return to_list_of_str(value, str.lower)

        # Default: return as string
        return to_str_if_value_else_empty_str(value, str.lower)

    def __get__(self, instance: Any, owner: type) -> Any:
        """
        This shouldn't be called since BaseConfig converts these to properties.
        """
        if instance is None:
            return self
        raise AttributeError(
            f"{self.__class__.__name__} {self.name} should have been converted to a property"
        )


class ConfField(BaseConfField):
    """
    Django-style configuration field descriptor.

    This class defines a configuration field that can be populated from either
    environment variables or TOML configuration files, with a fallback default value.

    Args:
        env: Environment variable name to read from
        toml: TOML key path (dot-separated) to read from
        default: Default value if neither source provides a value
    """

    def __init__(
        self,
        env: Optional[str] = None,
        toml: Optional[str] = None,
        default: Any = None,
    ):
        super().__init__()
        self.env = env
        self.toml = toml
        self.default = default

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the ConfField to the dictionary format expected by BaseConfig.

        Returns:
            A dict with keys: env, toml, default, name
        """
        return {
            "env": self.env,
            "toml": self.toml,
            "default": self.default,
            "name": self.name,
        }
