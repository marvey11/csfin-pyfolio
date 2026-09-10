from pathlib import Path

import pytest

from core.exceptions import RepositoryCorruptedError
from core.services import JsonPortfolioRepository


def test_missing_portfolio_is_empty(tmp_path: Path) -> None:
    assert JsonPortfolioRepository(tmp_path / "portfolio.json").load() is None


def test_corrupted_portfolio_raises_repository_error(tmp_path: Path) -> None:
    path = tmp_path / "portfolio.json"
    path.write_text("[{]", encoding="utf-8")

    with pytest.raises(RepositoryCorruptedError):
        JsonPortfolioRepository(path).load()
