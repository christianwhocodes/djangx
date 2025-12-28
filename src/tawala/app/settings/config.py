from os import environ
from pathlib import Path
from typing import Any, Dict, Optional, cast

from christianwhocodes.helpers import TypeConverter

from ... import PKG, PROJECT


class PackageConfig:
    def __init__(self) -> None:
        self.dir = PKG.dir
        self.name = PKG.name
        self.version = PKG.version


class ConfField:
    """
    Configuration field descriptor.

    This class defines a configuration field that can be populated from either
    environment variables or TOML configuration files, with a fallback default value.

    Args:
        env: Environment variable name to read from
        toml: TOML key path (dot-separated) to read from
        default: Default value if neither source provides a value
    """

    # Define which fields need special type handling
    _BOOL_FIELDS = {"debug", "pool", "use_vars"}
    _LIST_FIELDS = {"allowed_hosts", "configured_apps", "commands"}

    def __init__(
        self,
        env: Optional[str] = None,
        toml: Optional[str] = None,
        default: Any = None,
    ):
        self.name: Optional[str] = None
        self.env = env
        self.toml = toml
        self.default = default

    def __set_name__(self, owner: type, name: str) -> None:
        """Store the attribute name for type conversion."""
        self.name = name

    @property
    def dict(self) -> Dict[str, Any]:
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

    @staticmethod
    def convert_value(name: str, value: Any) -> Any:
        """
        Convert the raw value to the appropriate type based on field name.

        Args:
            value: Raw value from env or TOML

        Returns:
            Converted value of the appropriate type
        """
        # Handle None values with sensible defaults
        if value is None:
            if name in ConfField._BOOL_FIELDS:
                return False
            if name in ConfField._LIST_FIELDS:
                return []
            return ""

        # Handle boolean fields
        if name in ConfField._BOOL_FIELDS:
            return TypeConverter.to_bool(value)

        # Handle list fields
        if name in ConfField._LIST_FIELDS:
            return TypeConverter.to_list_of_str(value, str.lower)

        # Default: return as the value's type
        return value

    def __get__(self, instance: Any, owner: type) -> Any:
        """
        This shouldn't be called since BaseConfig converts these to properties.
        """
        if instance is None:
            return self
        raise AttributeError(
            f"{self.__class__.__name__} {self.name} should have been converted to a property"
        )


class ProjectConfig:
    """Base configuration class that handles loading from environment variables and TOML files."""

    _toml_data: dict[str, Any] = {}
    _config_specs: dict[str, dict[str, Any]] = {}
    _base_dir = PROJECT.base_dir

    def __init__(self) -> None:
        self.base_dir: Path = self._base_dir

    @staticmethod
    def _get_from_toml(
        key: Optional[str],
        default: Any = None,
    ) -> Any:
        """
        Get value from TOML configuration.

        Args:
            key: Dot-separated path to the config value (e.g., "storage.backend")
            default: Default value if key is not found

        Returns:
            The value from TOML, or the default if not found
        """

        if key is None:
            return default

        current: Any = PROJECT.toml_section
        for k in key.split("."):
            if isinstance(current, dict) and k in current:
                current = cast(Any, current[k])
            else:
                return default

        return current

    @classmethod
    def _fetch_value(
        cls,
        env_key: Optional[str] = None,
        toml_key: Optional[str] = None,
        default: Any = None,
    ) -> Any:
        """
        Fetch configuration value with fallback priority: ENV -> TOML -> default.

        Args:
            env_key: Environment variable name to check
            toml_key: TOML key path to check (dot-separated)
            default: Default value if neither source has the value

        Returns:
            The configuration value from the first available source (raw, no casting)
        """
        # Try environment variable first (if env_key is provided and exists)
        if env_key is not None and env_key in environ:
            return environ[env_key]

        # Fall back to TOML config and set default as it is the final fallback
        return cls._get_from_toml(toml_key, default=default)

    def __init_subclass__(cls) -> None:
        """
        Automatically convert ConfField descriptors to properties
        when a subclass is created.
        """
        super().__init_subclass__()
        cls._config_specs = dict(getattr(cls, "_config_specs", {}))

        for attr_name, attr_value in list(vars(cls).items()):
            # Skip private attributes, methods, and special descriptors
            if (
                attr_name.startswith("_")
                or callable(attr_value)
                or isinstance(attr_value, (classmethod, staticmethod, property))
            ):
                continue

            # Check if this is a BaseConfField (ConfField)
            if not isinstance(attr_value, ConfField):
                continue

            config_dict = attr_value.dict

            # Store the configuration spec for this field
            cls._config_specs[attr_name] = config_dict

            # Create property getter
            def make_getter(name: str, cfg: dict[str, Any], field: ConfField):
                def getter(self: "ProjectConfig") -> Any:
                    env_key = cfg["env"]
                    toml_key = cfg["toml"]
                    default = cfg["default"]
                    name = cfg["name"]
                    raw_value = self._fetch_value(env_key, toml_key, default)

                    # Convert to the appropriate type
                    return field.convert_value(name, raw_value)

                return getter

            setattr(
                cls,
                attr_name,
                property(make_getter(attr_name, config_dict, attr_value)),
            )

    @classmethod
    def list_env_keys(cls) -> list[str]:
        """List all environment variable keys used by this config class."""
        return [spec["env"] for spec in cls._config_specs.values() if spec.get("env") is not None]

    @classmethod
    def get_env_var_info(cls) -> list[dict[str, Any]]:
        """
        Get detailed information about all environment variables in this config class.

        Returns:
            List of dictionaries containing:
                - env_key: Environment variable name
                - toml_key: Corresponding TOML key path
                - default: Default value if any
                - name: Field name in the config class
        """
        vars_info: list[dict[str, Any]] = []

        for var_name, spec in cls._config_specs.items():
            env_key = spec.get("env")
            if env_key:  # Only include if it has an env key
                vars_info.append(
                    {
                        "env_key": env_key,
                        "toml_key": spec.get("toml"),
                        "default": spec.get("default"),
                        "name": var_name,
                    }
                )

        return vars_info


class SecurityConfig(ProjectConfig):
    """Security-related configuration settings."""

    secret_key = ConfField(env="SECRET_KEY", toml="secret-key")
    debug = ConfField(env="DEBUG", toml="debug", default=True)
    allowed_hosts = ConfField(env="ALLOWED_HOSTS", toml="allowed-hosts")


class DatabaseConfig(ProjectConfig):
    """Database configuration settings."""

    backend = ConfField(env="DB_BACKEND", toml="db.backend", default="sqlite3")
    service = ConfField(env="DB_SERVICE", toml="db.service")
    pool = ConfField(env="DB_POOL", toml="db.pool", default=False)
    ssl_mode = ConfField(env="DB_SSL_MODE", toml="db.ssl-mode", default="prefer")
    use_vars = ConfField(env="DB_USE_VARS", toml="db.use-vars", default=False)
    user = ConfField(env="DB_USER")
    password = ConfField(env="DB_PASSWORD")
    name = ConfField(env="DB_NAME")
    host = ConfField(env="DB_HOST")
    port = ConfField(env="DB_PORT")


class StorageConfig(ProjectConfig):
    """Storage configuration settings."""

    backend = ConfField(
        env="STORAGE_BACKEND",
        toml="storage.backend",
        default="filesystem",
    )
    token = ConfField(env="BLOB_READ_WRITE_TOKEN", toml="storage.token")


class CommandsConfig(ProjectConfig):
    """Install/Build Commands to be executed settings."""

    install = ConfField(env="COMMANDS_INSTALL", toml="commands.install")
    build = ConfField(env="COMMANDS_BUILD", toml="commands.build")


class TailwindCSSConfig(ProjectConfig):
    """TailwindCSS configuration settings."""

    version = ConfField(env="TAILWINDCSS_VERSION", toml="tailwindcss.version", default="v4.1.18")
    cli = ConfField(env="TAILWINDCSS_CLI", toml="tailwindcss.cli")
    source = ConfField(env="TAILWINDCSS_SOURCE", toml="tailwindcss.source")
    output = ConfField(env="TAILWINDCSS_OUTPUT", toml="tailwindcss.output")
