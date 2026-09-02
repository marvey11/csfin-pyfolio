from __future__ import annotations

import tempfile
from json import JSONDecodeError
from pathlib import Path
from typing import Protocol
from uuid import UUID

from pydantic import TypeAdapter

from core.models import Transaction
from core.services.stocks.repository import RepositoryCorruptedError

DEFAULT_TRANSACTIONS_PATH = Path("~/.codescape/pyfolio/transactions.json")
TransactionListAdapter = TypeAdapter(list[Transaction])


class TransactionRepository(Protocol):
    """Persistence interface for immutable transaction entities."""

    def get(self, transaction_id: UUID | str) -> Transaction | None: ...

    def list_all(self) -> list[Transaction]: ...

    def add(self, transaction: Transaction) -> None: ...

    def update(self, transaction: Transaction) -> None: ...

    def delete(self, transaction_id: UUID | str) -> None: ...


class JsonTransactionRepository:
    """Store transactions in a validated JSON array."""

    def __init__(self, json_path: Path) -> None:
        self.json_path = json_path.expanduser().resolve()
        self._cache: list[Transaction] | None = None

    def _get_data(self) -> list[Transaction]:
        if self._cache is not None:
            return self._cache

        if not self.json_path.exists():
            self.json_path.parent.mkdir(parents=True, exist_ok=True)
            self.json_path.touch()
            self._cache = []
            return self._cache

        try:
            content = self.json_path.read_text(encoding="utf-8").strip()
            self._cache = (
                [] if not content else TransactionListAdapter.validate_json(content)
            )
            return self._cache
        except (JSONDecodeError, ValueError) as err:
            raise RepositoryCorruptedError(
                f"Failed to parse repository file at '{self.json_path}': {err}"
            ) from err

    def _save_data(self) -> None:
        if self._cache is None:
            return
        json_bytes = TransactionListAdapter.dump_json(self._cache, indent=2) + b"\n"
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "wb", dir=self.json_path.parent, delete=False
        ) as tmp_file:
            tmp_file.write(json_bytes)
            tmp_path = Path(tmp_file.name)
        tmp_path.replace(self.json_path)

    @staticmethod
    def _normalise_id(transaction_id: UUID | str) -> UUID:
        return (
            transaction_id if isinstance(transaction_id, UUID) else UUID(transaction_id)
        )

    def get(self, transaction_id: UUID | str) -> Transaction | None:
        target_id = self._normalise_id(transaction_id)
        return next((item for item in self._get_data() if item.id == target_id), None)

    def list_all(self) -> list[Transaction]:
        return list(self._get_data())

    def add(self, transaction: Transaction) -> None:
        if self.get(transaction.id) is not None:
            raise ValueError(f"Transaction {transaction.id} already exists.")
        self._get_data().append(transaction)
        self._save_data()

    def update(self, transaction: Transaction) -> None:
        data = self._get_data()
        for index, existing in enumerate(data):
            if existing.id == transaction.id:
                data[index] = transaction
                self._save_data()
                return
        raise KeyError(f"Transaction {transaction.id} not found.")

    def delete(self, transaction_id: UUID | str) -> None:
        target_id = self._normalise_id(transaction_id)
        data = self._get_data()
        for index, transaction in enumerate(data):
            if transaction.id == target_id:
                del data[index]
                self._save_data()
                return
        raise KeyError(f"Transaction {target_id} not found.")
