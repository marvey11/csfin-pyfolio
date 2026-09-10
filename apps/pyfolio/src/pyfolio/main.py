from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from core.config import InvalidConfigurationError
from core.exceptions import InsufficientSharesError, RepositoryCorruptedError
from core.services import (
    ConfigurationService,
    JsonPortfolioRepository,
    JsonTransactionRepository,
    PortfolioService,
    TransactionService,
)

DEFAULT_PORTFOLIO_PATH = Path("~/.codescape/pyfolio/portfolio.json")

app = typer.Typer(name="pyfolio", help="Portfolio tracker", no_args_is_help=True)
console = Console()
err_console = Console(stderr=True)


def get_service(config_path: Path | None = None) -> PortfolioService:
    """Load transaction and portfolio repositories from application settings."""
    try:
        config = ConfigurationService.load(config_path)
        transaction_path = config.get_path(
            "transactions.json_path", Path("~/.codescape/pyfolio/transactions.json")
        )
        portfolio_path = config.get_path("portfolio.json_path", DEFAULT_PORTFOLIO_PATH)
        if transaction_path is None or portfolio_path is None:
            raise ValueError("'portfolio.json_path' must be configured.")
        transaction_service = TransactionService(
            JsonTransactionRepository(transaction_path)
        )
        return PortfolioService(
            transaction_service, JsonPortfolioRepository(portfolio_path)
        )
    except (FileNotFoundError, InvalidConfigurationError, ValueError) as err:
        err_console.print(f"[bold red]Configuration Error:[/bold red] {err}")
        raise typer.Exit(code=1) from err


@app.callback()
def main_callback(
    ctx: typer.Context,
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


def main() -> None:
    """Run the Pyfolio command-line application."""
    app()


if __name__ == "__main__":
    main()
