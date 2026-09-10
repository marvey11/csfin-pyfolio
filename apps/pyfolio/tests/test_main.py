import importlib
from decimal import Decimal
from pathlib import Path

from pytest import MonkeyPatch
from typer.testing import CliRunner

from core.models import Holding, Portfolio, StockMetadata
from pyfolio.main import app

runner = CliRunner()
main_module = importlib.import_module("pyfolio.main")


def test_portfolio_displays_active_holdings(monkeypatch: MonkeyPatch) -> None:
    class FakeService:
        def get_portfolio(self) -> Portfolio:
            return Portfolio(
                holdings=[
                    Holding(
                        stock=StockMetadata(isin="DE0007164600", name="SAP"),
                        active_shares=Decimal("2"),
                        cost_basis=Decimal("20"),
                        average_buy_price=Decimal("10"),
                        transaction_hash="hash",
                    )
                ]
            )

    def fake_get_service(config_path: Path | None) -> FakeService:
        return FakeService()

    monkeypatch.setattr(main_module, "get_service", fake_get_service)
    result = runner.invoke(app, ["portfolio"])

    assert result.exit_code == 0
    assert "DE0007164600" in result.output
    assert "SAP" in result.output


def test_portfolio_handles_empty_holdings(monkeypatch: MonkeyPatch) -> None:
    def fake_get_service(config_path: Path | None) -> _EmptyService:
        return _EmptyService()

    monkeypatch.setattr(main_module, "get_service", fake_get_service)
    result = runner.invoke(app, ["portfolio"])

    assert result.exit_code == 0
    assert "No active holdings found." in result.output


class _EmptyService:
    def get_portfolio(self) -> Portfolio:
        return Portfolio()
