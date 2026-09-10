from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from .stock_metadata import StockMetadata  # noqa: TC001


class PortfolioModel(BaseModel):
    """Base model using lossless string encoding for Decimal JSON values."""

    @field_serializer("*", when_used="json")
    def serialize_decimal(self, value: object) -> object:
        return str(value) if isinstance(value, Decimal) else value


class BuyLot(PortfolioModel):
    """An active FIFO purchase lot."""

    model_config = ConfigDict(validate_assignment=True)

    purchased_at: str
    shares: Decimal = Field(gt=0)
    price_per_share: Decimal
    cost_basis: Decimal


class Holding(PortfolioModel):
    """A stock holding assembled from active FIFO lots."""

    stock: StockMetadata
    active_shares: Decimal = Field(gt=0)
    cost_basis: Decimal
    average_buy_price: Decimal
    lots: list[BuyLot] = Field(default_factory=list[BuyLot])
    transaction_hash: str


class ClosedTrade(PortfolioModel):
    """A FIFO sale matched against one or more purchase lots."""

    stock: StockMetadata
    sold_at: str
    shares: Decimal = Field(gt=0)
    proceeds: Decimal
    cost_basis: Decimal
    realised_profit_loss: Decimal


class Portfolio(PortfolioModel):
    """Persisted portfolio holdings and realised trades."""

    holdings: list[Holding] = Field(default_factory=lambda: [])
    closed_trades: list[ClosedTrade] = Field(default_factory=list[ClosedTrade])
