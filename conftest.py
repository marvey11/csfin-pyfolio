from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from core.models import StockMetadata
from core.services.stocks import JsonStockRepository

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def sample_stock_sap() -> StockMetadata:
    """Pre-validated domain model for testing."""
    return StockMetadata(
        isin="DE0007164600",
        name="SAP SE",
        country_code="DE",
        currency_code="EUR",
    )


@pytest.fixture
def sample_stock_apple() -> StockMetadata:
    return StockMetadata(
        isin="US0378331005",
        name="Apple Inc.",
        country_code="US",
        currency_code="USD",
    )


@pytest.fixture
def mock_config_dir(tmp_path: Path) -> Path:
    """Provides a temporary, sandboxed configuration directory."""
    config_dir = tmp_path / ".codescape" / "pyfolio"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


@pytest.fixture
def mock_repo_path(mock_config_dir: Path) -> Path:
    return mock_config_dir / "stock_metadata.json"


@pytest.fixture
def empty_repo(mock_config_dir: Path) -> JsonStockRepository:
    """Provides a clean, isolated JsonStockRepository instance targeting a temp file."""
    json_path = mock_config_dir / "stock_metadata.json"
    return JsonStockRepository(json_path)


@pytest.fixture
def populated_repo(
    empty_repo: JsonStockRepository,
    sample_stock_sap: StockMetadata,
    sample_stock_apple: StockMetadata,
) -> JsonStockRepository:
    """Provides a JsonStockRepository pre-populated with sample domain data."""
    empty_repo.add(sample_stock_sap)
    empty_repo.add(sample_stock_apple)
    return empty_repo
