from pathlib import Path

import pdfplumber
from pdfplumber.page import Page


class PDFDocument:
    """Provide common page and text access for a PDF file."""

    def __init__(self, file_path: Path) -> None:
        """Load the pages belonging to ``file_path``."""
        self.file_path = file_path
        self.pages = self._extract_pages()

    def _extract_pages(self) -> list[Page]:
        """Extract pages from the PDF while its file handle is open."""
        with pdfplumber.open(self.file_path) as pdf:
            return [page for page in pdf.pages]

    def get_page(self, page_number: int) -> Page | None:
        """Return a zero-based page, or ``None`` for an invalid number."""
        return self.pages[page_number] if 0 <= page_number < len(self.pages) else None

    def get_text(self) -> str:
        """Extract and concatenate text from every page in the document."""
        with pdfplumber.open(self.file_path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
