from pathlib import Path

from core.models.transaction import Transaction
from parsers.pdf.base import BaseBankParser
from parsers.pdf.document import PDFDocument


class BankParserRegistry:
    """Register bank parsers and route PDF files to matching parsers."""

    def __init__(self) -> None:
        """Create an empty parser registry."""
        self._parsers: list[BaseBankParser] = []

    def register(self, parser: BaseBankParser) -> None:
        """Register ``parser`` in detection order."""
        self._parsers.append(parser)

    def find_parser(self, doc: PDFDocument) -> BaseBankParser | None:
        """Return the first parser that recognizes ``doc``."""
        for parser in self._parsers:
            if parser.can_parse(doc):
                return parser
        return None

    def parse_file(self, file_path: Path) -> list[Transaction]:
        """Detect and parse all transactions contained in ``file_path``."""
        doc = PDFDocument(file_path)
        parser = self.find_parser(doc)
        if not parser:
            raise ValueError(f"No matching bank parser found for {file_path.name}")
        return parser.parse(doc)
