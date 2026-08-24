from __future__ import annotations

from typing import TYPE_CHECKING

from core.models import StockMetadata
from stock_worker.main import app
from typer.testing import CliRunner

if TYPE_CHECKING:
    from pathlib import Path

    from core.repository import JsonStockRepository

runner = CliRunner()


# ============================================================================
# LIST Validation Tests
# ============================================================================


def test_cli_list_corrupted_json(mock_repo_path: Path) -> None:
    # Write invalid JSON with a trailing comma
    mock_repo_path.write_text(
        """{
        "DE0007164600": {
            "isin": "DE0007164600",
            "name": "SAP SE"
        },
    }"""
    )

    result = runner.invoke(app, ["list"])
    assert result.exit_code == 1
    assert "Format Error:" in result.output


def test_cli_list_empty(empty_repo: JsonStockRepository) -> None:
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No matching stocks found." in result.output


def test_cli_list_populated(populated_repo: JsonStockRepository) -> None:
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "- DE0007164600 (SAP SE) [DE] EUR" in result.output
    assert "- US0378331005 (Apple Inc.) [US] USD" in result.output


# ============================================================================
# ADD Validation Tests
# ============================================================================


def test_cli_add_stock_success(empty_repo: JsonStockRepository) -> None:
    result = runner.invoke(app, ["add", "DE0007164600", "--name", "SAP SE"])
    assert result.exit_code == 0
    assert empty_repo.get("DE0007164600") is not None


def test_cli_add_invalid_isin(empty_repo: JsonStockRepository) -> None:
    result = runner.invoke(app, ["add", "INVALID_ISIN"])

    assert result.exit_code == 1
    # CliRunner captures application output in stdout/output
    assert "Invalid ISIN format" in result.output


def test_cli_add_existing_stock(populated_repo: JsonStockRepository) -> None:
    result = runner.invoke(app, ["add", "DE0007164600", "--name", "SAP SE"])
    assert result.exit_code == 1
    assert "Stock DE0007164600 already exists" in result.output


# ============================================================================
# UPDATE Validation Tests
# ============================================================================


def test_cli_update_stock_success(empty_repo: JsonStockRepository) -> None:
    empty_repo.add(
        StockMetadata(
            isin="DE0007164600",
            name="UNKNOWN",
        )
    )

    stock_before = empty_repo.get("DE0007164600")
    assert stock_before is not None
    assert stock_before.name == "UNKNOWN"

    result = runner.invoke(app, ["update", "DE0007164600", "--name", "SAP SE"])
    assert result.exit_code == 0

    stock_after = empty_repo.get("DE0007164600")
    assert stock_after is not None
    assert stock_after.name == "SAP SE"


def test_cli_update_stock_not_found(empty_repo: JsonStockRepository) -> None:
    """Updating a stock will fail if the stock is not in the repository."""
    result = runner.invoke(app, ["update", "DE0007164600", "--name", "SAP SE"])
    assert result.exit_code == 1
    assert "Stock DE0007164600 not found" in result.output


# ============================================================================
# DELETE Validation Tests
# ============================================================================


def test_cli_delete_stock_success(populated_repo: JsonStockRepository) -> None:
    result = runner.invoke(app, ["delete", "DE0007164600"])
    assert result.exit_code == 0
    assert populated_repo.get("DE0007164600") is None


def test_cli_delete_stock_not_found(empty_repo: JsonStockRepository) -> None:
    result = runner.invoke(app, ["delete", "DE0007164600"])
    assert result.exit_code == 1
    assert "Stock DE0007164600 not found" in result.output
