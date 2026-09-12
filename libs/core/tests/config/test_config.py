"""Tests for Configuration class logic."""

import json
from pathlib import Path
from typing import Any

import pytest

from core.config import Configuration, InvalidConfigurationError


def test_configuration_initialization() -> None:
    config = Configuration()
    assert config.config == {}


def test_resolve_path_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_home: Path = tmp_path / "fakehome"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    resolved = Configuration.resolve_path()
    assert resolved == Configuration.DEFAULT_CONFIG_PATH.expanduser().resolve()


def test_from_json_success(tmp_path: Path) -> None:
    file_path = tmp_path / "config.json"
    content: dict[str, Any] = {
        "version": 1,
        "config": {"currency": "EUR", "settings": {"theme": "dark"}},
    }
    file_path.write_text(json.dumps(content))

    config = Configuration.from_json(file_path)
    assert config.get("currency") == "EUR"
    assert config.get("settings.theme") == "dark"


def test_from_json_invalid_corrupted(tmp_path: Path) -> None:
    file_path = tmp_path / "corrupt.json"
    file_path.write_text("{'version': 1,}")  # Invalid JSON syntax

    with pytest.raises(InvalidConfigurationError, match="Corrupted JSON"):
        Configuration.from_json(file_path)


def test_from_json_invalid_path(tmp_path: Path) -> None:
    file_path = tmp_path / "does_not_exist.json"
    assert not file_path.exists()

    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        Configuration.from_json(file_path)


def test_from_json_not_dict(tmp_path: Path) -> None:
    file_path = tmp_path / "not_dict.json"
    file_path.write_text(json.dumps([]))

    with pytest.raises(
        InvalidConfigurationError, match="Configuration root must be a JSON object"
    ):
        Configuration.from_json(file_path)


def test_from_json_invalid_schema(tmp_path: Path) -> None:
    file_path = tmp_path / "invalid_scgema.json"
    # `version` is a string (and does not represent an integer, either)
    file_path.write_text(json.dumps({"version": "1.23"}))

    with pytest.raises(InvalidConfigurationError, match="Schema validation failed"):
        Configuration.from_json(file_path)


def test_from_json_version_mismatch(tmp_path: Path) -> None:
    file_path = tmp_path / "old_version.json"
    file_path.write_text(json.dumps({"version": 99, "config": {}}))

    with pytest.raises(InvalidConfigurationError, match="Unsupported schema version"):
        Configuration.from_json(file_path)


def test_get_and_set_dot_notation() -> None:
    config = Configuration()
    config.set("app.server.port", 8080)

    assert config.get("app.server.port") == 8080
    assert config.get("app.missing", default="N/A") == "N/A"


def test_get_and_set_overwrite() -> None:
    """
    Tests that existing values are overwritten by a `dict` if they weren't a `dict`
    beforehand.
    """
    config = Configuration()
    config.set("app.server", "machine.locahost")

    assert config.get("app.server", "machine.localhost")

    config.set("app.server.hostname", "machine")
    config.set("app.server.port", 8080)

    assert config.get("app.server.hostname") == "machine"
    assert config.get("app.server.port") == 8080
