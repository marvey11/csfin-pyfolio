from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from core.models import StockMetadata
from core.repository import JsonStockRepository


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
def empty_repo(tmp_path: Path) -> JsonStockRepository:
    """Provides a fresh, empty JSON repository pointing to a temp file."""
    return JsonStockRepository(tmp_path / "stocks.json")


@pytest.fixture
def populated_repo(
    empty_repo: JsonStockRepository,
    sample_stock_sap: StockMetadata,
    sample_stock_apple: StockMetadata,
) -> JsonStockRepository:
    """Provides a repository pre-seeded with test stocks."""
    empty_repo.add(sample_stock_sap)
    empty_repo.add(sample_stock_apple)
    return empty_repo
