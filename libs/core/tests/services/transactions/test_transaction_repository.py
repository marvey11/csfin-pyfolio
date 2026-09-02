from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from core.models import StockMetadata, Transaction, TransactionType
from core.services import (
    JsonTransactionRepository,
    RepositoryCorruptedError,
    TransactionService,
)


def make_buy(name: str, transaction_date: date) -> Transaction:
    return Transaction(
        transaction_type=TransactionType.BUY,
        stock=StockMetadata(isin="DE0007164600", name=name),
        date=transaction_date,
        shares=Decimal("1"),
        price_per_share=Decimal("2"),
    )


def test_crud_replaces_and_persists_transaction(tmp_path: Path) -> None:
    path = tmp_path / "transactions.json"
    repository = JsonTransactionRepository(path)
    original = make_buy("SAP SE", date(2026, 9, 1))
    repository.add(original)

    replacement = original.model_copy(
        update={"stock": StockMetadata(isin="DE0007164600", name="SAP")}
    )
    repository.update(replacement)
    restored = JsonTransactionRepository(path).get(original.id)

    assert restored is not None
    assert restored.stock.name == "SAP"
    repository.delete(original.id)
    assert repository.list_all() == []


def test_corrupted_json_raises_repository_error(tmp_path: Path) -> None:
    path = tmp_path / "transactions.json"
    path.write_text("[{]", encoding="utf-8")

    with pytest.raises(RepositoryCorruptedError):
        JsonTransactionRepository(path).list_all()


def test_service_filters_by_name_type_and_date(tmp_path: Path) -> None:
    repository = JsonTransactionRepository(tmp_path / "transactions.json")
    repository.add(make_buy("SAP SE", date(2026, 9, 1)))
    repository.add(make_buy("SAP SE", date(2026, 9, 2)))

    results = TransactionService(repository).list_transactions(
        query="sap", start_date=date(2026, 9, 2), transaction_type="BUY"
    )

    assert len(results) == 1
    assert results[0].date == date(2026, 9, 2)
