from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from core.models import StockMetadata, Transaction, TransactionType
from core.utils import as_money
from parsers.pdf.base import BaseBankParser

from .parser_util import get_parsed_decimal

if TYPE_CHECKING:
    from core.services import StockService
    from parsers.pdf.document import PDFDocument


class ScalablePDFParser(BaseBankParser):
    """Parse Scalable Capital trade and dividend statements."""

    bank_id = "scalable"
    bank_name = "Scalable Capital"

    def __init__(self, stock_service: StockService) -> None:
        """Initialise the parser with its stock lookup service."""
        self.stock_service = stock_service

    def can_parse(self, doc: PDFDocument) -> bool:
        """Return whether ``doc`` contains Scalable Capital identification text."""
        text = doc.get_text()
        return "Scalable Capital Bank GmbH • Seitzstraße 8e, 80538 Munich" in text

    def parse(self, doc: PDFDocument) -> list[Transaction]:
        """Detect the statement type and return its normalized transaction."""

        text = doc.get_text()

        if re.search(r"^\s*Dividend\b", text, re.MULTILINE):
            return [self.parse_dividend_statement(text)]

        if re.search(r"^\s*Buy\b", text, re.MULTILINE) or re.search(r"\bDebit\b", text):
            return [self.parse_trade_statement(text, TransactionType.BUY)]

        if re.search(r"^\s*Sell\b", text, re.MULTILINE) or re.search(
            r"\bCredit\b", text
        ):
            return [self.parse_trade_statement(text, TransactionType.SELL)]

        raise ValueError(
            "Unrecognized document structure or unsupported transaction type."
        )

    def parse_trade_statement(self, text: str, tx_type: TransactionType) -> Transaction:
        """Parse a Scalable Capital buy or sell statement."""
        patterns = {
            "execution_time": r"Execution\s+(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2})",
            "quantity": r"(\d+(?:\.\d+)?)\s+pc\.",
            "price_per_share": r"pc\.\s+(\d+(?:\.\d+)?)\s+EUR",
            "net_total": r"pc\.\s+\d+(?:\.\d+)?\s+EUR\s+(\d+(?:\.\d+)?)\s+EUR",
            "isin": r"\b([A-Z]{2}[A-Z0-9]{9}\d)\b",
            "order_fees": r"Order fees\s+([+-]?\d+(?:\.\d+)?)\s+EUR",
            "gross_total": r"(?:Debit|Credit)\s+(\d+(?:\.\d+)?)\s+EUR",
            "to_be_taxed": r"To be taxed\s+(\d+(?:\.\d+)?)\s+EUR",
        }

        extracted: dict[str, str | None] = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.MULTILINE)
            extracted[key] = match.group(1) if match else None

        if not extracted["isin"] or not extracted["execution_time"]:
            raise ValueError("Failed to extract essential trade details (ISIN/Date).")

        exec_date = datetime.strptime(extracted["execution_time"], "%d.%m.%Y %H:%M:%S")
        shares = get_parsed_decimal(extracted, "quantity")
        price = get_parsed_decimal(extracted, "price_per_share")
        fees = get_parsed_decimal(extracted, "order_fees", default=Decimal("0"))
        taxes = get_parsed_decimal(extracted, "to_be_taxed", default=Decimal("0"))
        net_tot = get_parsed_decimal(extracted, "net_total")
        gross_tot = get_parsed_decimal(extracted, "gross_total")

        stock = self._get_stock(extracted["isin"])

        return Transaction(
            transaction_type=tx_type,
            stock=stock,
            date=exec_date,
            shares=shares,
            price_per_share=price,
            fees=as_money(fees),
            taxes=as_money(taxes),
            gross_total=as_money(gross_tot) if gross_tot else None,
            net_total=as_money(net_tot) if net_tot else None,
            total_cost=as_money(gross_tot) if gross_tot else None,
        )

    def parse_dividend_statement(self, text: str) -> Transaction:
        """Parse a Scalable Capital dividend statement."""
        patterns = {
            "isin": r"ISIN\s+([A-Z]{2}[A-Z0-9]{9}\d)",
            "entitled_quantity": r"Entitled quantity\s+(\d+(?:\.\d+)?)",
            "dates_raw": r"(\d{2}\.\d{2}\.\d{4})(\d{2}\.\d{2}\.\d{4})\s+Credit",
            "dividend_per_share": r"Credit\s+(\d+(?:\.\d+)?)\s+[A-Z]{3}",
            "exchange_rate": r"([A-Z]{3}\s+/\s+[A-Z]{3})\s+(\d+(?:\.\d+)?)",
            "gross_amount": (
                r"Credit\s+\d+(?:\.\d+)?\s+[A-Z]{3}\s+"
                r"\d+(?:\.\d+)?\s+(\d+(?:\.\d+)?)\s+EUR"
            ),
            "net_amount": r"Total\s+(\d+(?:\.\d+)?)\s+EUR",
        }

        extracted: dict[str, str | None] = {}
        for key, pattern in patterns.items():
            if key in ("dates_raw", "exchange_rate"):
                continue
            match = re.search(pattern, text)
            extracted[key] = match.group(1) if match else None

        if not extracted["isin"]:
            raise ValueError("Failed to extract ISIN from dividend statement.")

        # Parse concatenated Booking/Value dates (prefer Value Date for settled cash)
        date_match = re.search(patterns["dates_raw"], text)
        if date_match:
            val_date = datetime.strptime(date_match.group(2), "%d.%m.%Y").date()
        else:
            raise ValueError("Failed to parse transaction dates.")

        fx_match = re.search(patterns["exchange_rate"], text)
        fx_rate = Decimal(fx_match.group(2)) if fx_match else Decimal("1")

        eligible_shares = get_parsed_decimal(extracted, "entitled_quantity")
        div_per_share = get_parsed_decimal(extracted, "dividend_per_share")
        gross_tot = get_parsed_decimal(extracted, "gross_amount")
        net_tot = get_parsed_decimal(extracted, "net_amount")

        taxes = Decimal("0")
        if gross_tot is not None and net_tot is not None:
            taxes = gross_tot - net_tot

        stock = self._get_stock(extracted["isin"])

        return Transaction(
            transaction_type=TransactionType.DIVIDEND,
            stock=stock,
            date=val_date,
            eligible_shares=eligible_shares,
            dividend_per_share=div_per_share,
            fx_rate=fx_rate,
            taxes=as_money(taxes),
            gross_total=as_money(gross_tot) if gross_tot else None,
            net_total=as_money(net_tot) if net_tot else None,
        )

    def _get_stock(self, isin: str | None) -> StockMetadata:
        """Resolve an extracted ISIN through the configured stock service."""
        if not isin:
            raise ValueError("Failed to extract stock ISIN.")
        stock = self.stock_service.get(isin)
        if stock is None:
            raise ValueError(f"Stock {isin} not found.")
        return stock
