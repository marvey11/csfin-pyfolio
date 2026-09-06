from abc import ABC, abstractmethod

from core.models.transaction import Transaction
from parsers.pdf.document import PDFDocument


class BaseBankParser(ABC):
    """Interface implemented by bank-specific PDF transaction parsers."""

    bank_id: str
    bank_name: str

    @abstractmethod
    def can_parse(self, doc: PDFDocument) -> bool:
        """Inspects PDF text/metadata to verify if this parser handles the file."""
        ...

    @abstractmethod
    def parse(self, doc: PDFDocument) -> list[Transaction]:
        """Extracts and normalises transactions from the document."""
        ...
