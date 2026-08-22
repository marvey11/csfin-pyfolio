from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
from config import Configuration

if TYPE_CHECKING:
    from pathlib import Path


def test_from_json_loads_valid_file(tmp_path: Path) -> None:
    # Setup temporary file
    config_file = tmp_path / "config.json"
    data: dict[str, str | int] = {"schema_version": 1, "theme": "dark"}
    config_file.write_text(json.dumps(data), encoding="utf-8")

    # Act
    config = Configuration.from_json(config_file)

    # Assert
    assert config.config == data


def test_from_json_returns_defaults_when_file_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing_file = tmp_path / "non_existent.json"

    config = Configuration.from_json(missing_file)

    assert config.config == {}
    # Check that warning was printed to stderr
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_from_json_raises_value_error_on_invalid_json(tmp_path: Path) -> None:
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("{ broken json ", encoding="utf-8")

    with pytest.raises(ValueError, match="Failed to parse configuration JSON"):
        Configuration.from_json(invalid_file)


def test_from_json_raises_value_error_on_version_mismatch(tmp_path: Path) -> None:
    # Setup temporary file with mismatched schema_version
    config_file = tmp_path / "config.json"
    data: dict[str, str | int] = {"schema_version": 999, "theme": "dark"}
    config_file.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(ValueError, match="Configuration version mismatch"):
        Configuration.from_json(config_file)


def test_get_returns_default_when_key_missing() -> None:
    config = Configuration()
    default_value = "default"

    result = config.get("non_existent_key", default=default_value)
    assert result == default_value


def test_get_raises_key_error_when_key_missing_and_no_default() -> None:
    config = Configuration()

    with pytest.raises(KeyError):
        config.get("non_existent_key")


def test_get_returns_value_when_key_exists() -> None:
    config = Configuration()
    config.set("existing_key", "value")

    result = config.get("existing_key")
    assert result == "value"
