from __future__ import annotations

from typing import TYPE_CHECKING

from stock_worker.main import app
from typer.testing import CliRunner

if TYPE_CHECKING:
    from core.repository import JsonStockRepository

runner = CliRunner()


def test_cli_add_stock_success(mock_repo: JsonStockRepository) -> None:
    result = runner.invoke(app, ["add", "DE0007164600", "--name", "SAP SE"])
    assert result.exit_code == 0
    assert mock_repo.get("DE0007164600") is not None


def test_cli_add_invalid_isin() -> None:
    result = runner.invoke(app, ["add", "INVALID_ISIN"])
    assert result.exit_code == 1
    assert "Error:" in result.stderr
