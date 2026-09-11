"""Tests for ConfigurationService layer."""

from pathlib import Path

import pytest

from core.config import Configuration
from core.services import ConfigurationService


def test_service_get_and_set(tmp_path: Path) -> None:
    file_path = tmp_path / "config.json"
    config = Configuration()
    service = ConfigurationService(config)

    service.set_value("theme", "light", path=file_path)
    assert service.get_value("theme") == "light"
    assert file_path.exists()

    # Re-read to verify persistence
    reloaded_service = ConfigurationService.load(file_path)
    assert reloaded_service.get_value("theme") == "light"


def test_get_path_success(tmp_path: Path) -> None:
    config = Configuration()
    service = ConfigurationService(config)

    file_path = tmp_path / "abc"
    service.set_value("app_path", str(file_path))

    assert service.get_path("app_path") == file_path


def test_get_path_missing_key() -> None:
    config = Configuration()
    service = ConfigurationService(config)

    assert service.get_path("app_path") is None


def test_get_path_empty_string() -> None:
    config = Configuration()
    service = ConfigurationService(config)

    service.set_value("app_path", "   ")

    with pytest.raises(ValueError, match="must be a non-empty string path"):
        service.get_path("app_path")
