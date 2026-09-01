import datetime as dt
from pathlib import Path
from typing import Annotated

import typer
from core.config.config import Configuration
from core.models import StockMetadata
from core.services.stocks import (
    JsonStockRepository,
    RepositoryCorruptedError,
    StockService,
)

__version__ = "0.1.0"
__updated__ = "2026-08-24"


def main() -> None:
    typer.echo(get_version_message())
    typer.echo(f"Starting up -- {dt.datetime.now().strftime('%x %X')}")

    try:
        app()
    finally:
        typer.echo(f"Shutting down -- {dt.datetime.now().strftime('%x %X')}")


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


def get_service(config_path: Path | None = None) -> StockService:
    """Instantiate Configuration, JsonStockRepository, and StockService."""
    config = (
        Configuration.from_json(config_path)
        if config_path
        else Configuration.from_json()
    )
    stock_metadata_path = Path(str(config.get("stock_metadata_path", "")))
    typer.echo(f"Using path: {stock_metadata_path}")
    repo = JsonStockRepository(json_path=stock_metadata_path.expanduser())

    try:
        return StockService(repo)
    except RepositoryCorruptedError as err:
        typer.secho(f"Format Error: {err}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)


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


@app.command(name="list")
def list_stocks(
    ctx: typer.Context,
    query: Annotated[
        str | None,
        typer.Option("--query", "-q", help="Filter by ISIN or name substring"),
    ] = None,
    country: Annotated[
        str | None,
        typer.Option("--country", help="Filter by country code (e.g. DE, US)"),
    ] = None,
) -> None:
    """List stocks with optional search and country filtering."""

    config_path: Path | None = ctx.obj.get("config_path") if ctx.obj else None
    service = get_service(config_path)

    stocks = service.list_stocks(query=query, country_code=country)

    if not stocks:
        typer.echo("No matching stocks found.")
        return

    for stock in stocks:
        name_part = f" ({stock.name})" if stock.name else ""
        country_part = f" [{stock.country_code}]" if stock.country_code else ""
        currency_part = f" {stock.currency_code}" if stock.currency_code else ""
        typer.echo(f"- {stock.isin}{name_part}{country_part}{currency_part}")


@app.command()
def add(
    ctx: typer.Context,
    isin: Annotated[str, typer.Argument(help="The ISIN of the stock to add.")],
    name: Annotated[
        str | None,
        typer.Option("-n", "--name", help="The name of the stock to add."),
    ] = None,
    country: Annotated[
        str | None,
        typer.Option("--country", help="The 2-letter country code (e.g. DE, US, GB)."),
    ] = None,
    currency: Annotated[
        str | None,
        typer.Option(
            "--currency", help="The 3-letter currency code (e.g. EUR, USD, GBP)."
        ),
    ] = None,
) -> None:
    """Add a stock to the portfolio."""
    config_path: Path | None = ctx.obj.get("config_path") if ctx.obj else None
    service = get_service(config_path)

    try:
        stock = StockMetadata(
            isin=isin,
            name=name,
            country_code=country,
            currency_code=currency,
        )
        service.add_stock(stock)
        typer.echo(f"Successfully added stock: {stock.isin}")
    except (ValueError, KeyError) as err:
        typer.secho(f"Error: {err}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command()
def update(
    ctx: typer.Context,
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
    config_path: Path | None = ctx.obj.get("config_path") if ctx.obj else None
    service = get_service(config_path)

    try:
        stock = StockMetadata(
            isin=isin,
            name=name,
            country_code=country,
            currency_code=currency,
        )
        service.update_stock(stock)
        typer.echo(f"Successfully updated stock: {stock.isin}")
    except (ValueError, KeyError) as err:
        typer.secho(f"Error: {err}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command()
def delete(
    ctx: typer.Context,
    isin: Annotated[str, typer.Argument(help="The ISIN of the stock to delete.")],
) -> None:
    """Delete a stock from the portfolio."""
    config_path: Path | None = ctx.obj.get("config_path") if ctx.obj else None
    service = get_service(config_path)

    try:
        service.delete_stock(isin)
        typer.echo(f"Successfully deleted stock: {isin}")
    except (ValueError, KeyError) as err:
        typer.secho(f"Error: {err}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    main()
