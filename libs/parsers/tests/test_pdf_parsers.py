from datetime import datetime
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
    stock = StockMetadata(isin="FR0000121972", name="Schneider Electric")
    parser = ScalablePDFParser(make_stock_service(stock))
    text = """Contract note
    for client order
    Type MARKET Order ID SCALabcdefghijkl
    Execution 08.04.2026 10:19:19 Exchange ID 12345A67BCD89012
    Type Security Quantity Price Amount
    Sell Schneider Electric 1.399518 pc. 252.05 EUR 352.75 EUR
    FR0000121972
    Order fees -0.99 EUR
    Credit 351.76 EUR
    Contract note
    Sell 1.399518 pc. Schneider Electric
    Calculation of tax-relevant income
    Type Note Amount
    Profit 13.65 EUR
    Considered order fees -3.34 EUR
    To be taxed 0.00 EUR
    """

    transaction = parser.parse_trade_statement(text, TransactionType.BUY)

    assert transaction.stock is stock
    assert transaction.stock.name == "Schneider Electric"
    assert transaction.date == datetime(2026, 4, 8, 10, 19, 19)


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
    stock = StockMetadata(isin="US92826C8394", name="VISA Inc.")
    parser = ScalablePDFParser(make_stock_service(stock))
    text = """Dividend
    for period 01.01.2026 - 31.12.2026
    Entitled security VISA Inc.
    ISIN US92826C8394
    Entitled quantity 8
    Ex day 11.08.2026
    Booking Value date Type Amount / pcs. Entitled quantity Total amount
    Exchange rate
    31.08.202601.09.2026 Credit 0.67 USD 8 4.62 EUR
    USD / EUR 1.1608
    Foreign withholding tax -1.39 EUR
    Total 3.23 EUR
    """

    transaction = parser.parse_dividend_statement(text)

    assert transaction.transaction_type is TransactionType.DIVIDEND
    assert transaction.stock.name == "VISA Inc."
    assert transaction.net_total == Decimal("3.23")


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
