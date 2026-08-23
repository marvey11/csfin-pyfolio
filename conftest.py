from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from core.repository import JsonStockRepository, StockRepository

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def mock_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect home/config paths to a isolated temp directory for all tests."""
    config_dir = tmp_path / ".codescape" / "pyfolio"
    config_dir.mkdir(parents=True)
    monkeypatch.setenv("PYFOLIO_CONFIG_DIR", str(config_dir))
    return config_dir


@pytest.fixture
def mock_repo(
    mock_config_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> JsonStockRepository:
    """Redirects the CLI's get_repository function to a temp repository."""
    repo = JsonStockRepository(mock_config_dir / "stock_metadata.json")

    # Define a fully typed dummy function matching get_repository's signature
    def _fake_get_repository(config_path: Path | None = None) -> StockRepository:
        return repo

    monkeypatch.setattr("stock_worker.main.get_repository", _fake_get_repository)
    return repo
