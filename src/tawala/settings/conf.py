import builtins
import pathlib
from os import environ
from typing import Any, Optional, cast

from christianwhocodes.helpers import TypeConverter

from .. import PKG, PROJECT


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
        type: Type to convert the value to (str, bool, list, or Path)
    """

    def __init__(
        self,
        env: Optional[str] = None,
        toml: Optional[str] = None,
        type: type[str] | type[bool] | type[list[str]] | type[pathlib.Path] = str,
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
    def convert_value(value: Any, target_type: type) -> Any:
        """
        Convert the raw value to the appropriate type.

        Args:
            value: Raw value from env or TOML
            target_type: The type to convert to (str, bool, list[str], or Path)

        Returns:
            Converted value of the appropriate type
        """

        if value is None:
            match target_type:
                case builtins.list:
                    return []
                case builtins.str:
                    # instead of returning None, allows use of string methods in settings.py without checks
                    return ""
                case _:
                    return None
        else:
            match target_type:
                case builtins.bool:
                    return TypeConverter.to_bool(value)
                case pathlib.Path:
                    return TypeConverter.to_path(value)
                case builtins.list:
                    return TypeConverter.to_list_of_str(value, str.lower)
                case builtins.str:
                    return str(value)
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
        self.app_dir = self.base_dir / "app"
        self.api_dir = self.base_dir / "api"
        self.public_dir = self.base_dir / "public"

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
        if env_key is not None and env_key in environ:
            return environ[env_key]

        # Fall back to TOML config and set None as it is the final fallback
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
    allowed_hosts = ConfField(env="ALLOWED_HOSTS", toml="allowed-hosts", type=list)


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

    backend = ConfField(
        env="STORAGE_BACKEND",
        toml="storage.backend",
        type=str,
    )
    token = ConfField(env="BLOB_READ_WRITE_TOKEN", toml="storage.token", type=str)


class TailwindCSSConf(ProjectConf):
    """TailwindCSS configuration settings."""

    version = ConfField(
        env="TAILWINDCSS_VERSION",
        toml="tailwindcss.version",
        type=str,
    )
    cli = ConfField(
        env="TAILWINDCSS_CLI",
        toml="tailwindcss.cli",
        type=pathlib.Path,
    )


class CommandsConf(ProjectConf):
    """Install/Build Commands to be executed settings."""

    install = ConfField(env="COMMANDS_INSTALL", toml="commands.install", type=list)
    build = ConfField(env="COMMANDS_BUILD", toml="commands.build", type=list)
