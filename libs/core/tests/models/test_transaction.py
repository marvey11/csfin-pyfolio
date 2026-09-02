from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from core.models import StockMetadata, Transaction, TransactionType


@pytest.fixture
def stock() -> StockMetadata:
    return StockMetadata(isin="DE0007164600", name="SAP SE")


def test_buy_calculates_rounded_total_and_is_immutable(stock: StockMetadata) -> None:
    transaction = Transaction(
        transaction_type=TransactionType.BUY,
        stock=stock,
        date=date(2026, 9, 2),
        shares=Decimal("1.123456"),
        price_per_share=Decimal("10.123"),
        fees=Decimal("0.005"),
    )

    assert transaction.total_cost == Decimal("11.38")
    assert isinstance(transaction.id, UUID)
    with pytest.raises(ValidationError):
        transaction.fees = Decimal("2")


def test_sell_and_dividend_calculate_gross_and_net(stock: StockMetadata) -> None:
    sell = Transaction(
        transaction_type=TransactionType.SELL,
        stock=stock,
        date=date(2026, 9, 2),
        shares=Decimal("2"),
        price_per_share=Decimal("10.125"),
        fees=Decimal("0.10"),
        taxes=Decimal("0.20"),
    )
    dividend = Transaction(
        transaction_type=TransactionType.DIVIDEND,
        stock=stock,
        date=date(2026, 9, 2),
        eligible_shares=Decimal("10"),
        dividend_per_share=Decimal("1.1678"),
        fx_rate=Decimal("1.1678"),
        taxes=Decimal("0.15"),
    )

    assert sell.gross_total == Decimal("20.25")
    assert sell.net_total == Decimal("19.95")
    assert dividend.gross_total == Decimal("10.00")
    assert dividend.net_total == Decimal("9.85")


def test_split_and_spin_off_require_their_specific_fields(
    stock: StockMetadata,
) -> None:
    split = Transaction(
        transaction_type=TransactionType.SPLIT,
        stock=stock,
        date=date(2026, 9, 2),
        split_ratio=Decimal("4"),
    )
    spin_off = Transaction(
        transaction_type=TransactionType.SPIN_OFF,
        stock=stock,
        date=date(2026, 9, 2),
        cost_basis_allocation_ratio=Decimal("0.0484"),
        share_ratio=Decimal("1"),
        new_stock_isin="US0378331005",
    )

    assert split.split_ratio == Decimal("4")
    assert spin_off.new_stock_isin == "US0378331005"
    with pytest.raises(ValidationError, match="shares and price_per_share"):
        Transaction(
            transaction_type=TransactionType.BUY, stock=stock, date=date.today()
        )


def test_transaction_id_is_preserved_by_serialization(stock: StockMetadata) -> None:
    original = Transaction(
        transaction_type=TransactionType.BUY,
        stock=stock,
        date=date(2026, 9, 2),
        shares=Decimal("1"),
        price_per_share=Decimal("2"),
    )
    restored = Transaction.model_validate_json(original.model_dump_json())

    assert restored.id == original.id
    assert restored.date == original.date
