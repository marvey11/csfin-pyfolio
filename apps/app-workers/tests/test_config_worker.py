"""Tests for Typer CLI commands."""

from pathlib import Path

import pytest
from app_workers.config_worker import app
from typer.testing import CliRunner

from core.config import Configuration
from core.services import ConfigurationService

runner = CliRunner()


@pytest.fixture(autouse=True)
def mock_configuration_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Patch the worker with an isolated configuration service for each test."""
    service = ConfigurationService(Configuration())

    def fake_get_service(config_path: Path | None = None) -> ConfigurationService:
        return service

    monkeypatch.setattr("app_workers.config_worker.get_service", fake_get_service)


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "Portfolio Tracker version:" in result.stdout


def test_cli_set_and_get(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.touch()

    # Set value
    set_res = runner.invoke(app, ["-c", str(config_file), "set", "retries", "5"])
    assert set_res.exit_code == 0
    assert "Success" in set_res.stdout

    # Get value
    get_res = runner.invoke(app, ["-c", str(config_file), "get", "retries"])
    assert get_res.exit_code == 0
    assert "retries: 5" in get_res.stdout


def test_cli_get_missing_key(tmp_path: Path) -> None:
    config_file = tmp_path / "config.json"
    config_file.touch()
    result = runner.invoke(app, ["-c", str(config_file), "get", "nonexistent"])
    assert result.exit_code == 1
    assert "Warning" in result.stderr
