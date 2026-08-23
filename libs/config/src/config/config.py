import json
import sys
from pathlib import Path
from typing import Self

DEFAULT_CONFIG_PATH = Path("~/.codescape/pyfolio/settings.json").expanduser()


# Define a more descriptive type alias
type ConfigurationValue = str | int | dict[str, ConfigurationValue]


class Configuration:
    SCHEMA_VERSION = 1

    @classmethod
    def from_json(cls, json_path: Path = DEFAULT_CONFIG_PATH) -> Self:
        config = cls()

        if not json_path.exists():
            print(
                f"⚠️  Note: {json_path.name} not found. Using defaults.",
                file=sys.stderr,
            )
            return config

        try:
            with open(json_path, encoding="utf-8") as f:
                data: dict[str, ConfigurationValue] = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse configuration JSON: {e}") from e

        # Load raw data
        for k, v in data.items():
            config.set(str(k), v)

        config.check_version()

        return config

    @property
    def config(self) -> dict[str, ConfigurationValue]:
        return self._config

    def __init__(self) -> None:
        self._config: dict[str, ConfigurationValue] = {}

    def check_version(self) -> None:
        """Validates the 'schema_version' key. Raises ValueError if incompatible."""

        user_version = self.config.get("schema_version", 0)
        if user_version != self.SCHEMA_VERSION:
            raise ValueError(
                f"⚠️ Configuration version mismatch! "
                f"Expected {self.SCHEMA_VERSION}, found {user_version}."
            )

    def set(self, key: str, value: ConfigurationValue) -> None:
        self.config[key] = value

    def get(
        self, key: str, default: ConfigurationValue | None = None
    ) -> ConfigurationValue:
        """
        Gets a configuration value.
        If key is missing and no default is provided, raises KeyError.
        """
        if key not in self.config:
            if default is not None:
                return default
            raise KeyError(f"Configuration key '{key}' not found.")

        return self.config[key]
