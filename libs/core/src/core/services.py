from core.models import StockMetadata
from core.repository import StockRepository


class StockService:
    """Core domain service managing stock operations and query filtering."""

    def __init__(self, repository: StockRepository) -> None:
        # Validate repository integrity on creation
        repository.list_all()

        self.repository = repository

    def list_stocks(
        self,
        query: str | None = None,
        country_code: str | None = None,
    ) -> list[StockMetadata]:
        stocks = self.repository.list_all()

        if country_code:
            target = country_code.strip().upper()
            stocks = [s for s in stocks if s.country_code == target]

        if query:
            q = query.strip().lower()
            stocks = [s for s in stocks if q in s.isin.lower() or q in s.name.lower()]

        return stocks

    def add_stock(self, stock: StockMetadata) -> None:
        self.repository.add(stock)

    def update_stock(self, stock: StockMetadata) -> None:
        self.repository.update(stock)

    def delete_stock(self, isin: str) -> None:
        self.repository.delete(isin)
