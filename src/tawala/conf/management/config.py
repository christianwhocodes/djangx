import os
from typing import Any, Optional

from .fields import BaseConfField, ConfField
from .path import BasePath


class BaseConfig:
    """Base configuration class that handles loading from environment variables and TOML files."""

    _toml_data: dict[str, Any] = {}
    _config_specs: dict[str, dict[str, Any]] = {}

    @classmethod
    def _get_from_toml(
        cls,
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

        # Navigate through nested keys
        current: Optional[dict[str, Any]] = BasePath.get_cached_toml_section()
        for k in key.split("."):
            if current is not None and k in current:
                current = current[k]
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
        if env_key is not None and env_key in os.environ:
            return os.environ[env_key]

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
            if not isinstance(attr_value, BaseConfField):
                continue

            config_dict = attr_value.to_dict()

            # Store the configuration spec for this field
            cls._config_specs[attr_name] = config_dict

            # Create property getter
            def make_getter(name: str, cfg: dict[str, Any], field: BaseConfField):
                def getter(self: "BaseConfig") -> Any:
                    env_key = cfg["env"]
                    toml_key = cfg["toml"]
                    default = cfg["default"]
                    raw_value = self._fetch_value(env_key, toml_key, default)

                    # Convert to the appropriate type
                    return field.convert_value(raw_value)

                return getter

            setattr(
                cls,
                attr_name,
                property(make_getter(attr_name, config_dict, attr_value)),
            )

    @classmethod
    def list_env_keys(cls) -> list[str]:
        """List all environment variable keys used by this config class."""
        return [
            spec["env"]
            for spec in cls._config_specs.values()
            if spec.get("env") is not None
        ]

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


class SecurityConfig(BaseConfig):
    """Security-related configuration settings."""

    secret_key = ConfField(
        env="SECRET_KEY",
        toml="secret-key",
    )
    debug = ConfField(
        env="DEBUG",
        toml="debug",
        default=True,
    )
    allowed_hosts = ConfField(
        env="ALLOWED_HOSTS",
        toml="allowed-hosts",
    )


class ApplicationConfig(BaseConfig):
    """Application and URL configuration settings."""

    configured_apps = ConfField(
        env="CONFIGURED_APPS",
        toml="configured-apps",
    )


class DatabaseConfig(BaseConfig):
    """Database configuration settings."""

    backend = ConfField(
        env="DB_BACKEND",
        toml="db.backend",
        default="sqlite3",
    )
    service = ConfField(
        env="PG_SERVICE",
        toml="db.service",
    )
    pool = ConfField(
        env="DB_POOL",
        toml="db.pool",
        default=False,
    )
    ssl_mode = ConfField(
        env="DB_SSL_MODE",
        toml="db.ssl-mode",
        default="prefer",
    )
    use_vars = ConfField(
        env="DB_USE_VARS",
        toml="db.use-vars",
        default=False,
    )

    user = ConfField(env="DB_USER", default="postgres")
    password = ConfField(env="DB_PASSWORD")
    name = ConfField(env="DB_NAME", default="postgres")
    host = ConfField(env="DB_HOST", default="localhost")
    port = ConfField(env="DB_PORT", default="5432")


class StorageConfig(BaseConfig):
    """Storage configuration settings."""

    backend = ConfField(
        env="STORAGE_BACKEND",
        toml="storage.backend",
        default="filesystem",
    )
    token = ConfField(
        env="STORAGE_TOKEN",
        toml="storage.token",
    )


class BuildConfig(BaseConfig):
    """Build process configuration settings."""

    commands = ConfField(
        env="BUILD_COMMANDS",
        toml="build.commands",
    )
