from __future__ import annotations

from collections import defaultdict, deque
from decimal import Decimal
from typing import TYPE_CHECKING

from core.exceptions import InsufficientSharesError
from core.models import (
    BuyLot,
    ClosedTrade,
    Holding,
    Portfolio,
    StockMetadata,
    Transaction,
    TransactionType,
)
from core.services.portfolio.repository import PortfolioRepository, transaction_hash

if TYPE_CHECKING:
    from datetime import date, datetime

    from core.services.transactions.service import TransactionService


class PortfolioService:
    """Compute and cache a portfolio using FIFO tax-lot accounting."""

    def __init__(
        self,
        transaction_service: TransactionService,
        repository: PortfolioRepository,
    ) -> None:
        self.transaction_service = transaction_service
        self.repository = repository

    def get_portfolio(self) -> Portfolio:
        """Load a valid cache or recompute the portfolio from transactions."""
        transactions = sorted(
            self.transaction_service.list_transactions(),
            key=lambda item: (item.date, item.id.hex),
        )
        cached = self.repository.load()
        if cached is not None and self._cache_matches(cached, transactions):
            return cached

        portfolio = self._compute(transactions)
        self.repository.save(portfolio)
        return portfolio

    @staticmethod
    def _cache_matches(portfolio: Portfolio, transactions: list[Transaction]) -> bool:
        grouped: dict[str, list[Transaction]] = defaultdict(list)
        for transaction in transactions:
            grouped[transaction.stock.isin].append(transaction)
            if transaction.new_stock is not None:
                grouped[transaction.new_stock.isin].append(transaction)
            elif transaction.new_stock_isin is not None:
                grouped[transaction.new_stock_isin].append(transaction)
        return set(grouped) == {
            holding.stock.isin for holding in portfolio.holdings
        } and all(
            holding.transaction_hash == transaction_hash(grouped[holding.stock.isin])
            for holding in portfolio.holdings
        )

    def _compute(self, transactions: list[Transaction]) -> Portfolio:
        lots: dict[str, deque[BuyLot]] = defaultdict(deque)
        stocks: dict[str, StockMetadata] = {}
        closed_trades: list[ClosedTrade] = []

        for transaction in transactions:
            isin = transaction.stock.isin
            stocks[isin] = transaction.stock
            if transaction.transaction_type is TransactionType.BUY:
                if transaction.shares is None or transaction.price_per_share is None:
                    raise ValueError("BUY transaction is missing shares or price")
                cost_basis = transaction.total_cost or (
                    transaction.shares * transaction.price_per_share + transaction.fees
                )
                lots[isin].append(
                    BuyLot(
                        purchased_at=self._date_text(transaction.date),
                        shares=transaction.shares,
                        price_per_share=cost_basis / transaction.shares,
                        cost_basis=cost_basis,
                    )
                )
            elif transaction.transaction_type is TransactionType.SELL:
                closed_trades.append(self._sell(transaction, lots[isin]))
            elif transaction.transaction_type is TransactionType.SPLIT:
                if transaction.split_ratio is None:
                    raise ValueError("SPLIT transaction is missing split ratio")
                for lot in lots[isin]:
                    lot.shares *= transaction.split_ratio
                    lot.price_per_share /= transaction.split_ratio
            elif transaction.transaction_type is TransactionType.SPIN_OFF:
                self._spin_off(transaction, lots, stocks)

        holdings: list[Holding] = []
        for isin, active_lots in lots.items():
            if not active_lots:
                continue
            shares = sum((lot.shares for lot in active_lots), Decimal("0"))
            cost_basis = sum((lot.cost_basis for lot in active_lots), Decimal("0"))
            relevant = self._transactions_for_stock(isin, transactions)
            holdings.append(
                Holding(
                    stock=stocks[isin],
                    active_shares=shares,
                    cost_basis=cost_basis,
                    average_buy_price=cost_basis / shares,
                    lots=list(active_lots),
                    transaction_hash=transaction_hash(relevant),
                )
            )
        return Portfolio(holdings=holdings, closed_trades=closed_trades)

    def _sell(
        self, transaction: Transaction, active_lots: deque[BuyLot]
    ) -> ClosedTrade:
        if transaction.shares is None or transaction.price_per_share is None:
            raise ValueError("SELL transaction is missing shares or price")
        remaining = transaction.shares
        cost_basis = Decimal("0")
        while remaining > 0 and active_lots:
            lot = active_lots[0]
            consumed = min(remaining, lot.shares)
            cost_basis += lot.cost_basis * consumed / lot.shares
            if consumed == lot.shares:
                active_lots.popleft()
            else:
                lot.cost_basis -= lot.cost_basis * consumed / lot.shares
                lot.shares -= consumed
            remaining -= consumed
        if remaining > 0:
            raise InsufficientSharesError(
                f"Cannot sell {transaction.shares} shares of {transaction.stock.isin}; "
                f"{remaining} shares are unavailable. A BUY or split may be missing."
            )
        proceeds = transaction.gross_total or (
            transaction.shares * transaction.price_per_share
        )
        proceeds -= transaction.fees
        return ClosedTrade(
            stock=transaction.stock,
            sold_at=self._date_text(transaction.date),
            shares=transaction.shares,
            proceeds=proceeds,
            cost_basis=cost_basis,
            realised_profit_loss=proceeds - cost_basis,
        )

    @staticmethod
    def _spin_off(
        transaction: Transaction,
        lots: dict[str, deque[BuyLot]],
        stocks: dict[str, StockMetadata],
    ) -> None:
        if transaction.cost_basis_allocation_ratio is None:
            raise ValueError("SPIN_OFF transaction is missing allocation data")
        if transaction.share_ratio is None:
            raise ValueError("SPIN_OFF transaction is missing new stock data")
        new_stock = transaction.new_stock or StockMetadata(
            isin=transaction.new_stock_isin or ""
        )
        original_lots = lots[transaction.stock.isin]
        new_lots = lots[new_stock.isin]
        stocks[new_stock.isin] = new_stock
        for lot in original_lots:
            allocated = lot.cost_basis * transaction.cost_basis_allocation_ratio
            lot.cost_basis -= allocated
            lot.price_per_share = lot.cost_basis / lot.shares
            new_shares = lot.shares * transaction.share_ratio
            new_lots.append(
                BuyLot(
                    purchased_at=lot.purchased_at,
                    shares=new_shares,
                    price_per_share=allocated / new_shares,
                    cost_basis=allocated,
                )
            )

    @staticmethod
    def _date_text(value: date | datetime) -> str:
        return value.isoformat()

    @staticmethod
    def _transactions_for_stock(
        isin: str, transactions: list[Transaction]
    ) -> list[Transaction]:
        return [
            item
            for item in transactions
            if item.stock.isin == isin
            or (item.new_stock is not None and item.new_stock.isin == isin)
            or item.new_stock_isin == isin
        ]
