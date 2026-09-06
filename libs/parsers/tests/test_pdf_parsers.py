from decimal import Decimal
from pathlib import Path
from typing import ClassVar, Self, cast

import pytest

from core.models import StockMetadata, Transaction, TransactionType
from core.services import StockRepository, StockService
from parsers.pdf import BankParserRegistry, BaseBankParser, PDFDocument
from parsers.pdf.banks.scalable import ScalablePDFParser


class StubParser(BaseBankParser):
    """Parser stub used to verify registry ordering and routing."""

    bank_id = "stub"
    bank_name = "Stub Bank"

    def can_parse(self, doc: PDFDocument) -> bool:
        """Recognize every document in this test."""
        return True

    def parse(self, doc: PDFDocument) -> list[Transaction]:
        """Return no transactions for this test parser."""
        return []


class StubDocument:
    """Minimal document double for parser detection tests."""

    def __init__(self, text: str) -> None:
        self.text = text

    def get_text(self) -> str:
        """Return the configured document text."""
        return self.text


def make_stock_service(stock: StockMetadata) -> StockService:
    """Build a stock service backed by an in-memory repository."""
    stocks = {stock.isin: stock}

    class InMemoryStockRepository:
        def get(self, isin: str) -> StockMetadata | None:
            return stocks.get(isin)

        def list_all(self) -> list[StockMetadata]:
            return list(stocks.values())

        def add(self, stock: StockMetadata) -> None:
            stocks[stock.isin] = stock

        def update(self, stock: StockMetadata) -> None:
            stocks[stock.isin] = stock

        def delete(self, isin: str) -> None:
            del stocks[isin]

    return StockService(cast("StockRepository", InMemoryStockRepository()))


def test_registry_returns_first_matching_parser() -> None:
    registry = BankParserRegistry()
    parser = StubParser()
    registry.register(parser)

    assert registry.find_parser(cast("PDFDocument", StubDocument("text"))) is parser


def test_scalable_parser_uses_stock_service_metadata() -> None:
    stock = StockMetadata(isin="DE0007164600", name="SAP SE")
    parser = ScalablePDFParser(make_stock_service(stock))
    text = """Execution 01.02.2026 12:30:00
    2 pc. 100.00 EUR 200.00 EUR
    DE0007164600
    Order fees 1.00 EUR
    Debit 201.00 EUR
    """

    transaction = parser.parse_trade_statement(text, TransactionType.BUY)

    assert transaction.stock is stock
    assert transaction.stock.name == "SAP SE"


def test_scalable_parser_rejects_unknown_stock() -> None:
    parser = ScalablePDFParser(make_stock_service(StockMetadata(isin="US0378331005")))
    text = """Execution 01.02.2026 12:30:00
    2 pc. 100.00 EUR 200.00 EUR
    DE0007164600
    Debit 200.00 EUR
    """

    with pytest.raises(ValueError, match="Stock DE0007164600 not found"):
        parser.parse_trade_statement(text, TransactionType.BUY)


def test_scalable_parser_parses_dividend_statement() -> None:
    stock = StockMetadata(isin="DE0007164600", name="SAP SE")
    parser = ScalablePDFParser(make_stock_service(stock))
    text = """ISIN DE0007164600
    Entitled quantity 2
    01.02.202603.02.2026 Credit
    Credit 1.50 USD 3.00 2.70 EUR
    USD / EUR 0.90
    Total 2.40 EUR
    """

    transaction = parser.parse_dividend_statement(text)

    assert transaction.transaction_type is TransactionType.DIVIDEND
    assert transaction.stock.name == "SAP SE"
    assert transaction.net_total == Decimal("2.40")


def test_scalable_parser_rejects_unknown_document() -> None:
    parser = ScalablePDFParser(make_stock_service(StockMetadata(isin="DE0007164600")))

    with pytest.raises(ValueError, match="Unrecognized document structure"):
        parser.parse(cast("PDFDocument", StubDocument("Scalable Capital")))


def test_pdf_document_get_text_handles_textless_pages(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class Page:
        def extract_text(self) -> str | None:
            return None

    class PDF:
        pages: ClassVar[list[Page]] = [Page()]

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *args: object) -> None:
            return None

    def fake_open(_name: object) -> PDF:
        return PDF()

    monkeypatch.setattr("parsers.pdf.document.pdfplumber.open", fake_open)
    document = object.__new__(PDFDocument)
    document.file_path = tmp_path / "statement.pdf"

    assert document.get_text() == ""
