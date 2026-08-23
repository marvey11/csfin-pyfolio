import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Protocol

from config.config import Configuration
from core.models import StockMetadata
from core.repository import JsonStockRepository, StockRepository

__author__ = "Marco Wegner"
__email__ = "673439+marvey11@users.noreply.github.com"
__version__ = "0.1.0"
__date__ = "2026-08-22"
__updated__ = "2026-08-22"
__license__ = "MIT"


class AddArgs(Protocol):
    isin: str
    name: str | None
    country: str | None
    currency: str | None


class UpdateArgs(Protocol):
    isin: str
    name: str | None
    country: str | None
    currency: str | None


class DeleteArgs(Protocol):
    isin: str


def _get_version_message(short: bool = False) -> str:
    name = "stock-worker"
    template = (
        "{name} v{version} ({updated})"
        if short
        else "This is {name} version {version} (last updated {updated})"
    )
    return template.format(name=name, version=__version__, updated=__updated__)


def handle_add(args: Namespace, repo: StockRepository) -> None:
    stock = StockMetadata(
        isin=args.isin,
        name=getattr(args, "name", None),
        country_code=getattr(args, "country", None),
        currency_code=getattr(args, "currency", None),
    )
    repo.add(stock)
    print(f"Successfully added stock: {stock.isin}")


def handle_update(args: Namespace, repo: StockRepository) -> None:
    stock = StockMetadata(
        isin=args.isin,
        name=getattr(args, "name", None),
        country_code=getattr(args, "country", None),
        currency_code=getattr(args, "currency", None),
    )
    repo.update(stock)
    print(f"Successfully updated stock: {stock.isin}")


def handle_delete(args: Namespace, repo: StockRepository) -> None:
    repo.delete(args.isin)
    print(f"Successfully deleted stock: {args.isin}")


def main() -> int:

    print("Starting stock worker app...")

    config = Configuration.from_json()
    stock_metadata_path = Path(str(config.get("stock_metadata_path", None)))

    parser = _setup_cli()

    # Show top-level help if no subcommand or argument was provided
    if len(sys.argv) == 1:
        parser.print_help()
        return 0

    args = parser.parse_args()

    repo = JsonStockRepository(json_path=Path(stock_metadata_path).expanduser())

    # Execute subcommand action with dependency injection
    try:
        args.handler(args, repo)
    except (ValueError, KeyError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    print("Finished stock worker app...")

    return 0


def _setup_cli() -> ArgumentParser:
    parser = ArgumentParser(prog="stock-worker", description="Stock Worker")

    subparsers = parser.add_subparsers(
        title="sub-commands", dest="command", required=True, metavar="COMMAND"
    )

    parser.add_argument(
        "--version", action="version", version=_get_version_message(True)
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Optional path to the configuration file to override the default location",
        default=None,
    )

    add_parser = subparsers.add_parser("add", help="Add a stock to the portfolio")
    add_parser.add_argument("isin", type=str, help="The ISIN of the stock to add")
    add_parser.add_argument(
        "-n", "--name", type=str, help="The name of the stock to add"
    )
    add_parser.add_argument(
        "--country",
        type=str,
        help="The 2-letter country code of the stock's home country, e.g. DE, US, GB",
    )
    add_parser.add_argument(
        "--currency",
        type=str,
        help="The 3-letter currency code of the stock to add, e.g. EUR, USD, GBP",
    )
    add_parser.set_defaults(handler=handle_add)

    update_parser = subparsers.add_parser(
        "update", help="Update a stock in the portfolio"
    )
    update_parser.add_argument("isin", type=str, help="The ISIN of the stock to update")
    update_parser.add_argument(
        "-n", "--name", type=str, help="The name of the stock to update"
    )
    update_parser.add_argument(
        "--country",
        type=str,
        help="The 2-letter country code of the stock's home country, e.g. DE, US, GB",
    )
    update_parser.add_argument(
        "--currency",
        type=str,
        help="The 3-letter currency code of the stock to update, e.g. EUR, USD, GBP",
    )
    update_parser.set_defaults(handler=handle_update)

    delete_parser = subparsers.add_parser(
        "delete", help="Delete a stock from the portfolio"
    )
    delete_parser.add_argument("isin", type=str, help="The ISIN of the stock to delete")
    delete_parser.set_defaults(handler=handle_delete)

    return parser


if __name__ == "__main__":
    sys.exit(main())
