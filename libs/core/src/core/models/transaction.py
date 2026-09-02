from __future__ import annotations

from datetime import date, datetime  # noqa: TC003
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

from .stock_metadata import StockMetadata  # noqa: TC001

MONEY_PLACES = Decimal("0.01")


class TransactionType(StrEnum):
    """The supported portfolio transaction kinds."""

    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"
    SPLIT = "SPLIT"
    SPIN_OFF = "SPIN_OFF"


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


class Transaction(BaseModel):
    """An immutable portfolio transaction."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: UUID = Field(default_factory=uuid4)
    transaction_type: TransactionType = Field(
        validation_alias=AliasChoices("transaction_type", "type")
    )
    stock: StockMetadata
    date: date | datetime
    shares: Decimal | None = None
    price_per_share: Decimal | None = None
    fees: Decimal = Decimal("0")
    taxes: Decimal = Decimal("0")
    total_cost: Decimal | None = None
    eligible_shares: Decimal | None = None
    dividend_per_share: Decimal | None = None
    fx_rate: Decimal = Decimal("1")
    gross_total: Decimal | None = None
    net_total: Decimal | None = None
    split_ratio: Decimal | None = None
    cost_basis_allocation_ratio: Decimal | None = None
    share_ratio: Decimal | None = None
    new_stock: StockMetadata | None = None
    new_stock_isin: Annotated[str, Field(min_length=12, max_length=12)] | None = None

    @model_validator(mode="after")
    def calculate_values(self) -> Transaction:
        """Validate type-specific fields and calculate missing monetary values."""
        if self.transaction_type in (TransactionType.BUY, TransactionType.SELL):
            if self.shares is None or self.price_per_share is None:
                raise ValueError("shares and price_per_share are required")
            if self.transaction_type is TransactionType.BUY:
                if self.total_cost is None:
                    object.__setattr__(
                        self,
                        "total_cost",
                        _money(self.shares * self.price_per_share + self.fees),
                    )
            else:
                gross_total = self.gross_total
                if gross_total is None:
                    gross_total = _money(self.shares * self.price_per_share)
                    object.__setattr__(
                        self,
                        "gross_total",
                        gross_total,
                    )
                if self.net_total is None:
                    object.__setattr__(
                        self, "net_total", _money(gross_total - self.fees - self.taxes)
                    )
        elif self.transaction_type is TransactionType.DIVIDEND:
            if self.eligible_shares is None or self.dividend_per_share is None:
                raise ValueError("eligible_shares and dividend_per_share are required")
            if self.fx_rate <= 0:
                raise ValueError("fx_rate must be greater than zero")
            gross_total = self.gross_total
            if gross_total is None:
                gross_total = _money(
                    self.eligible_shares * self.dividend_per_share / self.fx_rate
                )
                object.__setattr__(
                    self,
                    "gross_total",
                    gross_total,
                )
            if self.net_total is None:
                object.__setattr__(self, "net_total", _money(gross_total - self.taxes))
        elif self.transaction_type is TransactionType.SPLIT:
            if self.split_ratio is None or self.split_ratio <= 0:
                raise ValueError("split_ratio must be greater than zero")
        elif self.transaction_type is TransactionType.SPIN_OFF:
            if self.cost_basis_allocation_ratio is None:
                raise ValueError("cost_basis_allocation_ratio is required")
            if self.share_ratio is None or self.share_ratio <= 0:
                raise ValueError("share_ratio must be greater than zero")
            if self.new_stock is None and self.new_stock_isin is None:
                raise ValueError("new_stock or new_stock_isin is required")

        return self

    @model_validator(mode="after")
    def round_supplied_values(self) -> Transaction:
        """Round all monetary values to cents, including caller-supplied values."""
        for field_name in ("fees", "taxes", "total_cost", "gross_total", "net_total"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _money(value))
        return self
