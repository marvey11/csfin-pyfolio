import datetime as dt
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from core.config import InvalidConfigurationError
from core.exceptions import RepositoryCorruptedError
from core.services import (
    ConfigurationService,
    JsonStockRepository,
    JsonTransactionRepository,
    StockService,
    TransactionService,
)
from parsers.pdf import BankParserRegistry
from parsers.pdf.banks.scalable import ScalablePDFParser

__version__ = "0.1.0"
__updated__ = "2026-09-05"


def main() -> None:
    console.print(get_version_message())
    console.print(f"Starting up -- {dt.datetime.now().strftime('%x %X')}")

    try:
        app()
    finally:
        console.print(f"Shutting down -- {dt.datetime.now().strftime('%x %X')}")


def get_service(config_path: Path | None = None) -> TransactionService:
    """Load configuration and create a transaction service for its repository."""

    try:
        config_service = ConfigurationService.load(config_path)
    except (FileNotFoundError, InvalidConfigurationError) as err:
        err_console.print(f"[bold red]Configuration Error:[/bold red] {err}")
        raise typer.Exit(code=1) from err

    transactions_path_value = config_service.get_value(
        "transactions.json_path", "~/.codescape/pyfolio/transactions.json"
    )
    if (
        not isinstance(transactions_path_value, str)
        or not transactions_path_value.strip()
    ):
        error_message = "'transactions.json_path' must be a non-empty string."
        err_console.print(f"[bold red]Configuration Error:[/bold red] {error_message}")
        raise typer.Exit(code=1)

    transactions_path = Path(transactions_path_value)
    repo = JsonTransactionRepository(json_path=transactions_path)

    try:
        return TransactionService(repository=repo)
    except RepositoryCorruptedError as err:
        err_console.print(f"[bold red]Format Error:[/bold red] {err}")
        raise typer.Exit(code=1) from err


def get_stock_service(config_path: Path | None = None) -> StockService:
    """Load configuration and create a stock service for ISIN resolution."""
    try:
        config_service = ConfigurationService.load(config_path)
    except (FileNotFoundError, InvalidConfigurationError) as err:
        err_console.print(f"[bold red]Configuration Error:[/bold red] {err}")
        raise typer.Exit(code=1) from err

    stocks_path_value = config_service.get_value(
        "stocks.json_path", "~/.codescape/pyfolio/stock_metadata.json"
    )
    if not isinstance(stocks_path_value, str) or not stocks_path_value.strip():
        error_message = "'stocks.json_path' must be a non-empty string."
        err_console.print(f"[bold red]Configuration Error:[/bold red] {error_message}")
        raise typer.Exit(code=1)

    try:
        return StockService(JsonStockRepository(Path(stocks_path_value)))
    except RepositoryCorruptedError as err:
        err_console.print(f"[bold red]Format Error:[/bold red] {err}")
        raise typer.Exit(code=1) from err


app = typer.Typer(
    name="pdf-transaction-worker",
    help="PDF Transaction Worker Application",
    no_args_is_help=True,
)
err_console = Console(stderr=True)
console = Console()


def get_version_message(short: bool = False) -> str:
    template = (
        "pdf-transaction-worker v{version} ({updated})"
        if short
        else "This is pdf-transaction-worker version {version} (last updated {updated})"
    )
    return template.format(version=__version__, updated=__updated__)


def version_callback(value: bool) -> None:
    if value:
        console.print(get_version_message(short=True))
        raise typer.Exit()


@app.callback()
def main_callback(
    ctx: typer.Context,
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Show application version and exit.",
        ),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            help="Optional path to configuration file.",
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
    ] = None,
) -> None:
    """Global CLI options and entry hook."""
    ctx.obj = {"config_path": config}


@app.command()
def parse(
    ctx: typer.Context,
    paths: Annotated[
        list[Path],
        typer.Argument(..., exists=True, file_okay=True, dir_okay=False, readable=True),
    ],
) -> None:
    """Parse bank PDF statements and store their transactions."""
    config_path: Path | None = ctx.obj.get("config_path") if ctx.obj else None
    transaction_service = get_service(config_path)
    stock_service = get_stock_service(config_path)
    registry = BankParserRegistry()
    registry.register(ScalablePDFParser(stock_service))

    try:
        for path in paths:
            for transaction in registry.parse_file(path):
                transaction_service.add(transaction)
                console.print(f"Successfully added transaction: {transaction.id}")
    except (ValueError, KeyError) as err:
        err_console.print(f"[bold red]Error:[/bold red] {err}")
        raise typer.Exit(code=1) from err


if __name__ == "__main__":
    main()
