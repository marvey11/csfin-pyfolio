from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from typer.testing import CliRunner

from app_workers import pdf_transaction_worker
from core.config import Configuration
from core.models import StockMetadata, Transaction, TransactionType


def test_parse_command_adds_transactions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The parse command stores each transaction returned by the registry."""
    stock = StockMetadata(isin="DE0007164600")
    transaction = Transaction(
        transaction_type=TransactionType.BUY,
        stock=stock,
        date=date(2026, 2, 1),
        shares=Decimal("2"),
        price_per_share=Decimal("100"),
    )
    added: list[Transaction] = []

    class Service:
        def add(self, item: Transaction) -> None:
            added.append(item)

    class Registry:
        def register(self, parser: object) -> None:
            pass

        def parse_file(self, file_path: Path) -> list[Transaction]:
            return [transaction]

    pdf_path = tmp_path / "statement.pdf"
    pdf_path.touch()

    def fake_get_service(_config_path: Path | None = None) -> Service:
        return Service()

    def fake_get_stock_service(_config_path: Path | None = None) -> object:
        return object()

    monkeypatch.setattr(pdf_transaction_worker, "get_service", fake_get_service)
    monkeypatch.setattr(
        pdf_transaction_worker, "get_stock_service", fake_get_stock_service
    )
    monkeypatch.setattr(pdf_transaction_worker, "BankParserRegistry", Registry)

    result = CliRunner().invoke(pdf_transaction_worker.app, ["parse", str(pdf_path)])

    assert result.exit_code == 0
    assert added == [transaction]
    assert "Successfully added transaction" in result.output


def test_get_service_uses_default_transaction_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The transaction service accepts a missing transactions path setting."""
    config_path = tmp_path / "settings.json"
    config_path.write_text('{"version": 1, "config": {}}', encoding="utf-8")
    monkeypatch.setenv("HOME", str(tmp_path))

    service = pdf_transaction_worker.get_service(config_path)

    assert service.list_transactions() == []


def test_get_stock_service_reads_configured_repository(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    stocks_path = tmp_path / "stocks.json"
    stocks_path.write_text("{}", encoding="utf-8")
    config_path = tmp_path / "settings.json"
    Configuration({"stocks": {"json_path": str(stocks_path)}}).to_json(config_path)

    service = pdf_transaction_worker.get_stock_service(config_path)

    assert service.list_stocks() == []
