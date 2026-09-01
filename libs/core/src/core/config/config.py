"""Configuration model definitions and serialization logic."""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError

# Recursive type alias for configuration values
type ConfigurationValue = str | int | dict[str, ConfigurationValue]

DEFAULT_CONFIG_PATH = Path("~/.codescape/pyfolio/settings.json")
CURRENT_SCHEMA_VERSION = 1


class InvalidConfigurationError(Exception):
    """Raised when the configuration is invalid or corrupted."""


class ConfigurationSchema(BaseModel):
    """Pydantic schema for validating configuration files."""

    version: int = Field(default=CURRENT_SCHEMA_VERSION)
    config: dict[str, ConfigurationValue] = Field(default_factory=dict)


class Configuration:
    """Encapsulates configuration state and file I/O operations."""

    def __init__(self, config: dict[str, ConfigurationValue] | None = None) -> None:
        """Initialise Configuration with an empty dict or pre-populated config data."""
        self.config: dict[str, ConfigurationValue] = (
            config if config is not None else {}
        )

    @classmethod
    def resolve_path(cls, path: Path | None = None) -> Path:
        """
        Resolve config path, defaulting to DEFAULT_CONFIG_PATH and expanding user dir.
        """
        target_path = path if path is not None else DEFAULT_CONFIG_PATH
        return target_path.expanduser().resolve()

    @classmethod
    def from_json(cls, path: Path | None = None) -> "Configuration":
        """Deserialize Configuration from a JSON file with validation."""
        resolved_path = cls.resolve_path(path)

        if not resolved_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {resolved_path}")

        try:
            with resolved_path.open("r", encoding="utf-8") as f:
                raw_data: Any = json.load(f)
        except json.JSONDecodeError as err:
            raise InvalidConfigurationError(
                f"Corrupted JSON in configuration file: {err}"
            ) from err

        print(f"raw_data: {raw_data}")  # Debugging output

        if not isinstance(raw_data, dict):
            raise InvalidConfigurationError("Configuration root must be a JSON object.")

        try:
            validated = ConfigurationSchema.model_validate(raw_data)
        except ValidationError as err:
            raise InvalidConfigurationError(f"Schema validation failed: {err}") from err

        if validated.version != CURRENT_SCHEMA_VERSION:
            raise InvalidConfigurationError(
                f"Unsupported schema version: {validated.version}. "
                f"Expected version {CURRENT_SCHEMA_VERSION}."
            )

        return cls(config=validated.config)

    def to_json(self, path: Path | None = None) -> None:
        """Serialize Configuration instance to a JSON file."""
        resolved_path = self.resolve_path(path)
        resolved_path.parent.mkdir(parents=True, exist_ok=True)

        schema = ConfigurationSchema(version=CURRENT_SCHEMA_VERSION, config=self.config)

        with resolved_path.open("w", encoding="utf-8") as f:
            json.dump(schema.model_dump(), f, indent=2)

    def get(
        self, key: str, default: ConfigurationValue | None = None
    ) -> ConfigurationValue | None:
        """Get a value from configuration using dot-notation for nested keys."""
        parts = key.split(".")
        current: dict[str, ConfigurationValue] | ConfigurationValue = self.config

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default

        return current

    def set(self, key: str, value: ConfigurationValue) -> None:
        """Set a value in configuration, supporting dot-notation for nested keys."""
        parts = key.split(".")
        current: dict[str, ConfigurationValue] = self.config

        for part in parts[:-1]:
            if (part not in current) or (not isinstance(current[part], dict)):
                current[part] = {}
            current = current[part]  # type: ignore[assignment]

        current[parts[-1]] = value
