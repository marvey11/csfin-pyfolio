"""Service layer for Configuration operations."""

from pathlib import Path

from core.config import Configuration, ConfigurationValue


class ConfigurationService:
    """Service providing safe getting and setting of Configuration parameters."""

    def __init__(self, config: Configuration) -> None:
        """Initialise service with a Configuration instance."""
        self._config = config

    @classmethod
    def load(cls, path: Path | None = None) -> "ConfigurationService":
        """Factory method to load configuration from file path."""
        config = Configuration.from_json(path)
        return cls(config)

    def save(self, path: Path | None = None) -> None:
        """Save the underlying configuration back to disk."""
        self._config.to_json(path)

    def get_value(
        self, key: str, default: ConfigurationValue | None = None
    ) -> ConfigurationValue | None:
        """Retrieve a configuration value by key."""
        return self._config.get(key, default)

    def get_path(self, key: str, default: Path | None = None) -> Path | None:
        """Retrieve a path-valued setting, expanding its user directory."""
        value = self.get_value(key)
        if value is None:
            return default.expanduser().resolve() if default is not None else None
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"'{key}' must be a non-empty string path.")
        return Path(value).expanduser().resolve()

    def set_value(
        self, key: str, value: ConfigurationValue, path: Path | None = None
    ) -> None:
        """Update a configuration value by key and persist changes to disk."""
        self._config.set(key, value)
        self.save(path)
