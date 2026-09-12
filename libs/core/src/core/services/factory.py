from core.services.portfolio.repository import JsonPortfolioRepository

from .config.service import ConfigurationService
from .stocks.repository import JsonStockRepository
from .transactions.repository import JsonTransactionRepository


class RepositoryFactory:
    """Composition helper to build repositories wired with config paths."""

    def __init__(self, config_service: ConfigurationService) -> None:
        self._config_service = config_service

    def create_stock_metadata_repo(self) -> JsonStockRepository:
        json_path = self._config_service.get_path("stocks.json_path")
        return JsonStockRepository(json_path)

    def create_transaction_repo(self) -> JsonTransactionRepository:
        json_path = self._config_service.get_path("transactions.json_path")
        return JsonTransactionRepository(json_path)

    def create_portfolio_repo(self) -> JsonPortfolioRepository:
        json_path = self._config_service.get_path("portfolio.json_path")
        return JsonPortfolioRepository(json_path)
