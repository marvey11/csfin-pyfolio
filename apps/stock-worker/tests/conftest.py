from pathlib import Path

import pytest
import typer
from core.repository import RepositoryCorruptedError, StockRepository


@pytest.fixture(autouse=True)
def mock_repo(
    empty_repo: StockRepository, monkeypatch: pytest.MonkeyPatch
) -> StockRepository:
    """
    Automatically redirects get_repository to the isolated empty_repo fixture for all
    CLI tests.
    """

    def _fake_get_repository(config_path: Path | None = None) -> StockRepository:
        try:
            # Mirror the validation trigger performed in main.py get_repository
            empty_repo.list_all()
        except RepositoryCorruptedError as err:
            typer.secho(f"Format Error: {err}", err=True, fg=typer.colors.RED)
            raise typer.Exit(code=1)
        return empty_repo

    monkeypatch.setattr("stock_worker.main.get_repository", _fake_get_repository)
    return empty_repo
