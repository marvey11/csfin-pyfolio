from __future__ import annotations

from typing import TYPE_CHECKING

from core.models import Transaction, TransactionType

if TYPE_CHECKING:
    from datetime import date, datetime
    from uuid import UUID

    from .repository import TransactionRepository


class TransactionService:
    """Service for transaction CRUD operations and filtering."""

    def __init__(self, repository: TransactionRepository) -> None:
        """Initialise the service and validate the repository."""
        repository.list_all()
        self.repository = repository

    def get(self, transaction_id: UUID | str) -> Transaction | None:
        """Get one transaction by immutable identifier."""
        return self.repository.get(transaction_id)

    def list_transactions(
        self,
        query: str | None = None,
        start_date: date | datetime | None = None,
        end_date: date | datetime | None = None,
        transaction_type: TransactionType | str | None = None,
        stock_isin: str | None = None,
    ) -> list[Transaction]:
        """Return transactions matching the supplied optional filters."""
        transactions = self.repository.list_all()
        if query:
            needle = query.strip().lower()
            transactions = [
                item
                for item in transactions
                if needle in item.stock.isin.lower()
                or (item.stock.name is not None and needle in item.stock.name.lower())
            ]
        if stock_isin:
            target_isin = stock_isin.strip().upper()
            transactions = [
                item for item in transactions if item.stock.isin == target_isin
            ]
        if transaction_type:
            target_type = TransactionType(transaction_type)
            transactions = [
                item for item in transactions if item.transaction_type is target_type
            ]
        if start_date is not None:
            transactions = [item for item in transactions if item.date >= start_date]
        if end_date is not None:
            transactions = [item for item in transactions if item.date <= end_date]
        return transactions

    def add(self, transaction: Transaction) -> None:
        """Add a transaction."""
        self.repository.add(transaction)

    def update(self, transaction: Transaction) -> None:
        """Replace a transaction with the same identifier."""
        self.repository.update(transaction)

    def delete(self, transaction_id: UUID | str) -> None:
        """Delete a transaction by identifier."""
        self.repository.delete(transaction_id)
