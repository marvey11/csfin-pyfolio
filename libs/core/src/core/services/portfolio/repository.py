from __future__ import annotations

import tempfile
from hashlib import sha256
from json import JSONDecodeError
from pathlib import Path
from typing import Protocol

from pydantic import TypeAdapter

from core.exceptions import RepositoryCorruptedError
from core.models import Portfolio, Transaction

PortfolioAdapter = TypeAdapter(Portfolio)


class PortfolioRepository(Protocol):
    """Persistence interface for computed portfolios."""

    def load(self) -> Portfolio | None: ...

    def save(self, portfolio: Portfolio) -> None: ...


class JsonPortfolioRepository:
    """Store a validated portfolio document and its transaction cache."""

    DEFAULT_DATA_PATH = Path("~/.codescape/pyfolio")
    DEFAULT_PORTFOLIO_PATH = DEFAULT_DATA_PATH / "portfolio.json"

    def __init__(self, json_path: Path | None = None) -> None:
        self.json_path = (
            (json_path if json_path is not None else self.DEFAULT_PORTFOLIO_PATH)
            .expanduser()
            .resolve()
        )

    def load(self) -> Portfolio | None:
        """Load the cached portfolio, returning ``None`` for an empty file."""
        if not self.json_path.exists():
            return None
        try:
            content = self.json_path.read_text(encoding="utf-8").strip()
            if not content:
                return None
            return PortfolioAdapter.validate_json(content)
        except (JSONDecodeError, ValueError) as err:
            raise RepositoryCorruptedError(
                f"Failed to parse portfolio file at '{self.json_path}': {err}"
            ) from err

    def save(self, portfolio: Portfolio) -> None:
        """Atomically persist a validated portfolio document."""
        payload = PortfolioAdapter.dump_json(portfolio, indent=2) + b"\n"
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "wb", dir=self.json_path.parent, delete=False
        ) as tmp_file:
            tmp_file.write(payload)
            tmp_path = Path(tmp_file.name)
        tmp_path.replace(self.json_path)


def transaction_hash(transactions: list[Transaction]) -> str:
    """Return a stable SHA-256 hash for a transaction collection."""
    values = [transaction.model_dump(mode="json") for transaction in transactions]
    values.sort(key=lambda value: (str(value.get("date")), str(value.get("id"))))
    encoded = TypeAdapter(list[dict[str, object]]).dump_json(values, by_alias=True)
    return sha256(encoded).hexdigest()
