from pathlib import Path

import pytest
import typer
from core.repository import RepositoryCorruptedError, StockRepository
from core.services import StockService


@pytest.fixture(autouse=True)
def mock_service(empty_repo: StockRepository, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Automatically patches get_service in stock_worker.main to instantiate
    a StockService backed by the isolated empty_repo fixture.
    """

    def _fake_get_service(config_path: Path | None = None) -> StockService:
        try:
            return StockService(empty_repo)
        except RepositoryCorruptedError as err:
            typer.secho(f"Format Error: {err}", err=True, fg=typer.colors.RED)
            raise typer.Exit(code=1)

    monkeypatch.setattr("stock_worker.main.get_service", _fake_get_service)
