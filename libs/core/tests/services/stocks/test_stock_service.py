from pathlib import Path

from core.models import StockMetadata
from core.services import JsonStockRepository, StockService

STOCK_DE01 = StockMetadata(
    isin="DE1234567890", name="DE Test 01", country_code="DE", currency_code="EUR"
)
STOCK_DE02 = StockMetadata(
    isin="DE9876543210", name="DE Test 02", country_code="DE", currency_code="EUR"
)
STOCK_NL01 = StockMetadata(
    isin="NL1234567890", name="NL Test 01", country_code="NL", currency_code="EUR"
)
STOCK_NL02 = StockMetadata(
    isin="NL9876543210", name="NL Test 02", country_code="NL", currency_code="EUR"
)


def service(tmp_path: Path, stocks: list[StockMetadata]) -> StockService:
    repository = JsonStockRepository(tmp_path / "stock_metadata.json")
    for stock in stocks:
        repository.add(stock)
    return StockService(repository)


def test_list_stocks_empty(tmp_path: Path) -> None:
    result = service(tmp_path, []).list_stocks()

    assert len(result) == 0


def test_list_stocks_by_country(tmp_path: Path) -> None:
    result = service(
        tmp_path, [STOCK_DE01, STOCK_DE02, STOCK_NL01, STOCK_NL02]
    ).list_stocks(country_code="NL")

    assert len(result) == 2

    isins = [x.isin for x in result]

    assert STOCK_NL01.isin in isins
    assert STOCK_NL02.isin in isins


def test_list_stocks_by_country_not_found(tmp_path: Path) -> None:
    result = service(
        tmp_path, [STOCK_DE01, STOCK_DE02, STOCK_NL01, STOCK_NL02]
    ).list_stocks(country_code="CA")

    assert len(result) == 0


def test_list_stocks_by_query(tmp_path: Path) -> None:
    result = service(
        tmp_path, [STOCK_DE01, STOCK_DE02, STOCK_NL01, STOCK_NL02]
    ).list_stocks(query="TEST")

    assert len(result) == 4

    isins = [x.isin for x in result]

    assert STOCK_NL01.isin in isins
    assert STOCK_NL02.isin in isins
    assert STOCK_DE01.isin in isins
    assert STOCK_DE02.isin in isins


def test_list_stocks_by_query_not_found(tmp_path: Path) -> None:
    result = service(
        tmp_path, [STOCK_DE01, STOCK_DE02, STOCK_NL01, STOCK_NL02]
    ).list_stocks(query="XyZ")

    assert len(result) == 0
