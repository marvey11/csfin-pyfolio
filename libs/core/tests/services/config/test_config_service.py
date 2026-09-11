"""Tests for ConfigurationService layer."""

from pathlib import Path

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
