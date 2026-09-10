from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from core.exceptions import InsufficientSharesError
from core.models import StockMetadata, Transaction, TransactionType
from core.services import (
    JsonPortfolioRepository,
    JsonTransactionRepository,
    PortfolioService,
    TransactionService,
)

STOCK = StockMetadata(isin="DE0007164600", name="SAP")


def transaction(
    transaction_type: TransactionType,
    transaction_date: date,
    shares: str,
    price: str,
    fees: str = "0",
) -> Transaction:
    return Transaction(
        transaction_type=transaction_type,
        stock=STOCK,
        date=transaction_date,
        shares=Decimal(shares),
        price_per_share=Decimal(price),
        fees=Decimal(fees),
    )


def service(tmp_path: Path, transactions: list[Transaction]) -> PortfolioService:
    transaction_repository = JsonTransactionRepository(tmp_path / "transactions.json")
    for item in transactions:
        transaction_repository.add(item)
    return PortfolioService(
        TransactionService(transaction_repository),
        JsonPortfolioRepository(tmp_path / "portfolio.json"),
    )


def test_fifo_lots_and_realised_profit_include_fees(tmp_path: Path) -> None:
    result = service(
        tmp_path,
        [
            transaction(TransactionType.BUY, date(2026, 1, 1), "2", "10", "2"),
            transaction(TransactionType.BUY, date(2026, 1, 2), "3", "20"),
            transaction(TransactionType.SELL, date(2026, 1, 3), "3", "30", "1"),
        ],
    ).get_portfolio()

    assert result.holdings[0].active_shares == Decimal("2")
    assert result.holdings[0].cost_basis == Decimal("40")
    assert result.closed_trades[0].cost_basis == Decimal("42")
    assert result.closed_trades[0].realised_profit_loss == Decimal("47")


def test_overselling_raises_domain_error(tmp_path: Path) -> None:
    with pytest.raises(InsufficientSharesError, match="BUY or split"):
        service(
            tmp_path,
            [transaction(TransactionType.SELL, date(2026, 1, 1), "1", "10")],
        ).get_portfolio()


def test_split_preserves_cost_basis_and_adjusts_lot_price(tmp_path: Path) -> None:
    split = Transaction(
        transaction_type=TransactionType.SPLIT,
        stock=STOCK,
        date=date(2026, 1, 2),
        split_ratio=Decimal("2"),
    )
    result = service(
        tmp_path,
        [transaction(TransactionType.BUY, date(2026, 1, 1), "2", "10"), split],
    ).get_portfolio()

    assert result.holdings[0].active_shares == Decimal("4")
    assert result.holdings[0].cost_basis == Decimal("20")
    assert result.holdings[0].average_buy_price == Decimal("5")


def test_spin_off_creates_new_holding_and_allocates_cost_basis(tmp_path: Path) -> None:
    new_stock = StockMetadata(isin="US0378331005", name="Apple")
    spin_off = Transaction(
        transaction_type=TransactionType.SPIN_OFF,
        stock=STOCK,
        date=date(2026, 1, 2),
        share_ratio=Decimal("1"),
        cost_basis_allocation_ratio=Decimal("0.25"),
        new_stock=new_stock,
    )
    result = service(
        tmp_path,
        [transaction(TransactionType.BUY, date(2026, 1, 1), "2", "10"), spin_off],
    ).get_portfolio()

    holdings = {holding.stock.isin: holding for holding in result.holdings}
    assert holdings[STOCK.isin].cost_basis == Decimal("15.00")
    assert holdings[new_stock.isin].active_shares == Decimal("2")
    assert holdings[new_stock.isin].cost_basis == Decimal("5.00")


def test_cached_portfolio_round_trips_as_decimal_strings(tmp_path: Path) -> None:
    first = service(
        tmp_path,
        [transaction(TransactionType.BUY, date(2026, 1, 1), "2", "10")],
    ).get_portfolio()
    second = service(tmp_path, []).get_portfolio()

    assert second == first
    assert '"cost_basis": "20.00"' in (tmp_path / "portfolio.json").read_text()
