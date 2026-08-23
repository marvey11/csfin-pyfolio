import tempfile
from pathlib import Path
from typing import Protocol

from pydantic import TypeAdapter, ValidationError

from .models import StockMetadata


class StockRepository(Protocol):
    def get(self, isin: str) -> StockMetadata | None: ...

    def add(self, stock: StockMetadata) -> None: ...

    def update(self, stock: StockMetadata) -> None: ...

    def delete(self, isin: str) -> None: ...


# Create an alias for readability
StockDictAdapter = TypeAdapter(dict[str, StockMetadata])


class JsonStockRepository:
    def __init__(self, json_path: Path) -> None:
        self.json_path = json_path
        self._cache: dict[str, StockMetadata] | None = None

    def _get_data(self) -> dict[str, StockMetadata]:
        if self._cache is None:
            if not self.json_path.exists() or self.json_path.stat().st_size == 0:
                self._cache = {}
            else:
                try:
                    self._cache = StockDictAdapter.validate_json(
                        self.json_path.read_bytes()
                    )
                except ValidationError:
                    self._cache = {}
        return self._cache

    def _save_data(self) -> None:
        if self._cache is None:
            return

        json_bytes = (
            StockDictAdapter.dump_json(self._cache, indent=2, exclude_none=True) + b"\n"
        )
        self.json_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            "wb", dir=self.json_path.parent, delete=False
        ) as tmp_file:
            tmp_file.write(json_bytes)
            tmp_path = Path(tmp_file.name)

        tmp_path.replace(self.json_path)

    def get(self, isin: str) -> StockMetadata | None:
        return self._get_data().get(isin)

    def list_all(self) -> list[StockMetadata]:
        return list(self._get_data().values())

    def add(self, stock: StockMetadata) -> None:
        data = self._get_data()
        if stock.isin in data:
            raise ValueError(f"Stock {stock.isin} already exists.")
        data[stock.isin] = stock
        self._save_data()

    def update(self, stock: StockMetadata) -> None:
        data = self._get_data()
        if stock.isin not in data:
            raise KeyError(f"Stock {stock.isin} not found.")

        updated_stock = data[stock.isin].update(stock)
        data[stock.isin] = (
            updated_stock if updated_stock is not None else data[stock.isin]
        )
        self._save_data()

    def delete(self, isin: str) -> None:
        data = self._get_data()
        if isin not in data:
            raise KeyError(f"Stock {isin} not found.")
        del data[isin]
        self._save_data()
