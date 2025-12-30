import builtins
import pathlib
from typing import Any, Literal, Optional, cast

from christianwhocodes.helpers import TypeConverter
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from .. import ENV, PKG, PROJECT


class PackageConf:
    def __init__(self) -> None:
        self.pkg_dir: pathlib.Path = PKG.dir
        self.pkg_name: str = PKG.name
        self.pkg_version: str = PKG.version


class ConfField:
    """
    Configuration field descriptor.

    This class defines a configuration field that can be populated from either
    environment variables or TOML configuration files.

    Args:
        env: Environment variable name to read from
        toml: TOML key path (dot-separated) to read from
        type: Type to convert the value to. Supports:
            - str, bool, pathlib.Path
            - "email" for validated email strings
            - list[str] for list of strings
            - list["email"] for list of validated emails
    """

    def __init__(
        self,
        env: Optional[str] = None,
        toml: Optional[str] = None,
        type: (
            type[str]
            | type[bool]
            | type[list[str]]
            | type[pathlib.Path]
            | Literal["email"]
            | Literal["list[str]"]
            | Literal["list[email]"]
        ) = str,
    ):
        self.name: Optional[str] = None
        self.env = env
        self.toml = toml
        self.type = type

    def __set_name__(self, owner: type, name: str) -> None:
        """Store the attribute name for type conversion."""
        self.name = name

    @property
    def dict(self) -> dict[str, Any]:
        """
        Convert the ConfField to the dictionary format expected by BaseConfig.

        Returns:
            A dict with keys: env, toml, name, type
        """
        return {
            "env": self.env,
            "toml": self.toml,
            "name": self.name,
            "type": self.type,
        }

    @staticmethod
    def validate_email_value(value: Any) -> str:
        """
        Validate a single email address using Django's validator.

        Args:
            value: Email address to validate

        Returns:
            The validated email string

        Raises:
            ValueError: If the email is invalid
        """
        if value is None or value == "":
            return ""

        email_str = str(value).strip()
        try:
            validate_email(email_str)
            return email_str
        except ValidationError as e:
            raise ValueError(f"Invalid email address '{email_str}': {e.message}")

    @staticmethod
    def parse_list_type(type_spec: Any) -> tuple[bool, Optional[str]]:
        """
        Parse a type specification to determine if it's a list and what the item type is.

        Args:
            type_spec: Type specification (e.g., list[str], "list[email]", list)

        Returns:
            Tuple of (is_list, item_type) where item_type is "str", "email", or None
        """
        # Handle string type specifications like "list[str]" or "list[email]"
        if isinstance(type_spec, str):
            if type_spec.startswith("list[") and type_spec.endswith("]"):
                item_type = type_spec[5:-1]  # Extract content between "list[" and "]"
                return (True, item_type)
            return (False, None)

        # Handle actual type objects like list[str]
        if type_spec is builtins.list:
            return (True, "str")  # Default to str for backwards compatibility

        return (False, None)

    @staticmethod
    def convert_value(value: Any, target_type: Any) -> Any:
        """
        Convert the raw value to the appropriate type.

        Args:
            value: Raw value from env or TOML
            target_type: The type to convert to

        Returns:
            Converted value of the appropriate type
        """
        # Parse if this is a list type
        is_list, item_type = ConfField.parse_list_type(target_type)

        # Handle None values
        if value is None:
            if is_list:
                return []
            elif target_type == "email" or target_type is str:
                return ""
            else:
                return None

        # Handle list types
        if is_list:
            # Convert to list of strings first
            string_list = TypeConverter.to_list_of_str(value, str.strip)

            # Then validate/convert each item based on item_type
            if item_type == "email":
                validated_emails: list[str] = []
                for email in string_list:
                    if email:  # Skip empty strings
                        validated_emails.append(ConfField.validate_email_value(email))
                return validated_emails
            else:  # item_type == "str" or None (default to str)
                return string_list

        # Handle scalar types
        match target_type:
            case builtins.bool:
                return TypeConverter.to_bool(value)
            case pathlib.Path:
                return TypeConverter.to_path(value)
            case builtins.str:
                return str(value)
            case "email":
                return ConfField.validate_email_value(value)
            case _:
                raise ValueError(f"Unsupported target type: {target_type}")

    def __get__(self, instance: Any, owner: type) -> Any:
        """
        This shouldn't be called since BaseConfig converts these to properties.
        """
        if instance is None:
            return self
        raise AttributeError(
            f"{self.__class__.__name__} {self.name} should have been converted to a property"
        )


class ProjectConf:
    """Base configuration class that handles loading from environment variables and TOML files."""

    _toml_section: dict[str, Any] = PROJECT.toml_section

    def __init__(self) -> None:
        self.base_dir: pathlib.Path = PROJECT.dir

    @classmethod
    def _get_from_toml(cls, key: Optional[str]) -> Any:
        """
        Get value from TOML configuration.

        Args:
            key: Dot-separated path to the config value (e.g., "storage.backend")

        Returns:
            The value from TOML, or None if not found
        """

        if key is None:
            return None
        else:
            current: Any = cls._toml_section
            for k in key.split("."):
                if isinstance(current, dict) and k in current:
                    current = cast(Any, current[k])
                else:
                    return None

            return current

    @classmethod
    def _fetch_value(
        cls,
        env_key: Optional[str] = None,
        toml_key: Optional[str] = None,
    ) -> Any:
        """
        Fetch configuration value with fallback priority: ENV -> TOML -> None.

        Args:
            env_key: Environment variable name to check
            toml_key: TOML key path to check (dot-separated)

        Returns:
            The configuration value from the first available source (raw, no casting)
        """
        # Try environment variable first (if env_key is provided and exists)
        if env_key is not None and env_key in ENV:
            return ENV[env_key]

        # Else fall back to TOML config and set None as it is the final fallback
        else:
            return cls._get_from_toml(toml_key)

    def __init_subclass__(cls) -> None:
        """
        Automatically convert ConfField descriptors to properties
        when a subclass is created.
        """
        super().__init_subclass__()

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

            config_dict = attr_value.dict

            # Create property getter
            def make_getter(name: str, cfg: dict[str, Any]):
                def getter(self: "ProjectConf") -> Any:
                    env_key = cfg["env"]
                    toml_key = cfg["toml"]
                    target_type = cfg["type"]
                    raw_value = self._fetch_value(env_key, toml_key)

                    # Convert to the appropriate type
                    return ConfField.convert_value(raw_value, target_type)

                return getter

            setattr(
                cls,
                attr_name,
                property(make_getter(attr_name, config_dict)),
            )


class SecurityConf(ProjectConf):
    """Security-related configuration settings."""

    secret_key = ConfField(env="SECRET_KEY", toml="secret-key", type=str)
    debug = ConfField(env="DEBUG", toml="debug", type=bool)
    allowed_hosts = ConfField(env="ALLOWED_HOSTS", toml="allowed-hosts", type="list[str]")


class AppConf(ProjectConf):
    """Site-related configuration settings."""

    name = ConfField(env="APP_NAME", toml="app.name", type=str)
    short_name = ConfField(env="APP_SHORT_NAME", toml="app.short-name", type=str)
    description = ConfField(env="APP_DESCRIPTION", toml="app.description", type=str)


class DatabaseConf(ProjectConf):
    """Database configuration settings."""

    backend = ConfField(env="DB_BACKEND", toml="db.backend", type=str)
    service = ConfField(env="DB_SERVICE", toml="db.service", type=str)
    pool = ConfField(env="DB_POOL", toml="db.pool", type=bool)
    ssl_mode = ConfField(env="DB_SSL_MODE", toml="db.ssl-mode", type=str)
    use_vars = ConfField(env="DB_USE_VARS", toml="db.use-vars", type=bool)
    user = ConfField(env="DB_USER", type=str)
    password = ConfField(env="DB_PASSWORD", type=str)
    name = ConfField(env="DB_NAME", type=str)
    host = ConfField(env="DB_HOST", type=str)
    port = ConfField(env="DB_PORT", type=str)


class StorageConf(ProjectConf):
    """Storage configuration settings."""

    backend = ConfField(env="STORAGE_BACKEND", toml="storage.backend", type=str)
    token = ConfField(env="BLOB_READ_WRITE_TOKEN", toml="storage.token", type=str)


class TailwindCSSConf(ProjectConf):
    """TailwindCSS configuration settings."""

    version = ConfField(env="TAILWINDCSS_VERSION", toml="tailwindcss.version", type=str)
    cli = ConfField(env="TAILWINDCSS_CLI", toml="tailwindcss.cli", type=pathlib.Path)


class CommandsConf(ProjectConf):
    """Install/Build Commands to be executed settings."""

    install = ConfField(env="COMMANDS_INSTALL", toml="commands.install", type="list[str]")
    build = ConfField(env="COMMANDS_BUILD", toml="commands.build", type="list[str]")


class EmailConf(ProjectConf):
    """Email configuration settings."""

    backend = ConfField(env="EMAIL_BACKEND", toml="email.backend", type=str)
    host = ConfField(env="EMAIL_HOST", toml="email.host", type=str)
    port = ConfField(env="EMAIL_PORT", toml="email.port", type=str)
    use_tls = ConfField(env="EMAIL_USE_TLS", toml="email.use-tls", type=bool)
    host_user = ConfField(env="EMAIL_HOST_USER", toml="email.host-user", type=str)
    host_password = ConfField(env="EMAIL_HOST_PASSWORD", toml="email.host-password", type=str)


class ContactAddressConf(ProjectConf):
    """Contact Address configuration settings."""

    country = ConfField(env="CONTACT_ADDRESS_COUNTRY", toml="contact.address.country", type=str)
    state = ConfField(env="CONTACT_ADDRESS_STATE", toml="contact.address.state", type=str)
    city = ConfField(env="CONTACT_ADDRESS_CITY", toml="contact.address.city", type=str)
    street = ConfField(env="CONTACT_ADDRESS_STREET", toml="contact.address.street", type=str)


class ContactEmailConf(ProjectConf):
    """Contact Email configuration settings."""

    primary = ConfField(env="CONTACT_EMAIL_PRIMARY", toml="contact.email.primary", type="email")
    additional = ConfField(
        env="CONTACT_EMAIL_ADDITIONAL",
        toml="contact.email.additional",
        type="list[email]",
    )


class ContactNumberConf(ProjectConf):
    """Contact Phone Number configuration settings."""

    primary = ConfField(env="CONTACT_NUMBER_PRIMARY", toml="contact.number.primary", type=str)
    additional = ConfField(
        env="CONTACT_NUMBER_ADDITIONAL",
        toml="contact.number.additional",
        type="list[str]",
    )
