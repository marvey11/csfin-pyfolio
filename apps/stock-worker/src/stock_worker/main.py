from pathlib import Path
from typing import Annotated

import typer
from config.config import Configuration
from core.models import StockMetadata
from core.repository import JsonStockRepository, StockRepository

__author__ = "Marco Wegner"
__email__ = "673439+marvey11@users.noreply.github.com"
__version__ = "0.1.0"
__date__ = "2026-08-22"
__updated__ = "2026-08-23"
__license__ = "MIT"


app = typer.Typer(
    name="stock-worker",
    help="Stock Worker Application",
    no_args_is_help=True,
)


def get_version_message(short: bool = False) -> str:
    template = (
        "stock-worker v{version} ({updated})"
        if short
        else "This is stock-worker version {version} (last updated {updated})"
    )
    return template.format(version=__version__, updated=__updated__)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(get_version_message(short=True))
        raise typer.Exit()


def get_repository(config_path: Path | None = None) -> StockRepository:
    """Helper to initialize the repository using Configuration."""
    config = Configuration.from_json()
    stock_metadata_path = Path(str(config.get("stock_metadata_path", None)))
    return JsonStockRepository(json_path=stock_metadata_path.expanduser())


@app.callback()
def main_callback(
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
    pass


@app.command()
def add(
    isin: Annotated[str, typer.Argument(help="The ISIN of the stock to add.")],
    name: Annotated[
        str | None,
        typer.Option("-n", "--name", help="The name of the stock to add."),
    ] = None,
    country: Annotated[
        str | None,
        typer.Option(
            "--country",
            help="The 2-letter country code (e.g. DE, US, GB).",
        ),
    ] = None,
    currency: Annotated[
        str | None,
        typer.Option(
            "--currency",
            help="The 3-letter currency code (e.g. EUR, USD, GBP).",
        ),
    ] = None,
) -> None:
    """Add a stock to the portfolio."""
    repo = get_repository()
    try:
        stock = StockMetadata(
            isin=isin,
            name=name,
            country_code=country,
            currency_code=currency,
        )
        repo.add(stock)
        typer.echo(f"Successfully added stock: {stock.isin}")
    except (ValueError, KeyError) as err:
        typer.secho(f"Error: {err}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command()
def update(
    isin: Annotated[str, typer.Argument(help="The ISIN of the stock to update.")],
    name: Annotated[
        str | None,
        typer.Option("-n", "--name", help="The name of the stock to update."),
    ] = None,
    country: Annotated[
        str | None,
        typer.Option(
            "--country",
            help="The 2-letter country code (e.g. DE, US, GB).",
        ),
    ] = None,
    currency: Annotated[
        str | None,
        typer.Option(
            "--currency",
            help="The 3-letter currency code (e.g. EUR, USD, GBP).",
        ),
    ] = None,
) -> None:
    """Update a stock in the portfolio."""
    repo = get_repository()
    try:
        stock = StockMetadata(
            isin=isin,
            name=name,
            country_code=country,
            currency_code=currency,
        )
        repo.update(stock)
        typer.echo(f"Successfully updated stock: {stock.isin}")
    except (ValueError, KeyError) as err:
        typer.secho(f"Error: {err}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command()
def delete(
    isin: Annotated[str, typer.Argument(help="The ISIN of the stock to delete.")],
) -> None:
    """Delete a stock from the portfolio."""
    repo = get_repository()
    try:
        repo.delete(isin)
        typer.echo(f"Successfully deleted stock: {isin}")
    except (ValueError, KeyError) as err:
        typer.secho(f"Error: {err}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
