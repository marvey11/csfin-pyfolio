from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from core.config import InvalidConfigurationError
from core.exceptions import InsufficientSharesError, RepositoryCorruptedError
from core.services import (
    ConfigurationService,
    PortfolioService,
    RepositoryFactory,
    TransactionService,
)

__version__ = "0.1.0"
__updated__ = "2026-09-12"


def main() -> None:
    """Run the Pyfolio command-line application."""

    console.print(get_version_message())
    console.print(f"Starting up -- {datetime.now().strftime('%x %X')}")

    try:
        app()
    finally:
        console.print(f"Shutting down -- {datetime.now().strftime('%x %X')}")


app = typer.Typer(name="pyfolio", help="Portfolio tracker", no_args_is_help=True)
console = Console()
err_console = Console(stderr=True)


def get_version_message(short: bool = False) -> str:
    template = (
        "stock-worker v{version} ({updated})"
        if short
        else "This is stock-worker version {version} (last updated {updated})"
    )
    return template.format(version=__version__, updated=__updated__)


def version_callback(value: bool) -> None:
    if value:
        console.print(get_version_message(short=True))
        raise typer.Exit()


def get_service(config_path: Path | None = None) -> PortfolioService:
    """Load transaction and portfolio repositories from application settings."""
    try:
        config_service = ConfigurationService.load(config_path)
    except (FileNotFoundError, InvalidConfigurationError) as err:
        err_console.print(f"[bold red]Configuration Error:[/bold red] {err}")
        raise typer.Exit(code=1) from err

    factory = RepositoryFactory(config_service)

    transaction_repo = factory.create_transaction_repo()
    portfolio_repo = factory.create_portfolio_repo()

    try:
        transaction_service = TransactionService(transaction_repo)
        return PortfolioService(transaction_service, portfolio_repo)
    except (FileNotFoundError, InvalidConfigurationError, ValueError) as err:
        err_console.print(f"[bold red]Configuration Error:[/bold red] {err}")
        raise typer.Exit(code=1) from err


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
    """Global application options."""
    ctx.obj = {"config_path": config}


@app.command()
def portfolio(ctx: typer.Context) -> None:
    """Compute or load the portfolio and display active holdings."""
    config_path: Path | None = ctx.obj.get("config_path") if ctx.obj else None
    try:
        result = get_service(config_path).get_portfolio()
    except InsufficientSharesError as err:
        err_console.print(f"[bold yellow]Portfolio Warning:[/bold yellow] {err}")
        raise typer.Exit(code=1) from err
    except RepositoryCorruptedError as err:
        err_console.print(f"[bold red]Format Error:[/bold red] {err}")
        raise typer.Exit(code=1) from err

    if not result.holdings:
        console.print("No active holdings found.")
        return

    table = Table("ISIN", "Name", "Shares", "Cost Basis", "Average Buy Price")
    for holding in result.holdings:
        table.add_row(
            holding.stock.isin,
            holding.stock.name or "",
            str(holding.active_shares),
            str(holding.cost_basis),
            str(holding.average_buy_price),
        )
    console.print(table)


if __name__ == "__main__":
    main()
