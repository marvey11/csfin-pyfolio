"""Command Line Interface worker for managing configuration."""

import datetime as dt
import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from core.config import Configuration, ConfigurationValue, InvalidConfigurationError
from core.services import ConfigurationService

__version__ = "0.1.0"
__updated__ = "2026-09-02"


def main() -> None:
    console.print(get_version_message())
    console.print(f"Starting up -- {dt.datetime.now().strftime('%x %X')}")

    try:
        app()
    finally:
        console.print(f"Shutting down -- {dt.datetime.now().strftime('%x %X')}")


app = typer.Typer(
    name="config-worker",
    help="pyfolio CLI configuration worker.",
    no_args_is_help=True,
)
err_console = Console(stderr=True)
console = Console()


def get_version_message(short: bool = False) -> str:
    template = (
        "config-worker v{version} ({updated})"
        if short
        else "This is config-worker version {version} (last updated {updated})"
    )
    return template.format(version=__version__, updated=__updated__)


def version_callback(value: bool) -> None:
    """Callback for printing program version."""
    if value:
        console.print(
            f"[bold cyan]Portfolio Tracker[/bold cyan] version: "
            f"[green]{__version__}[/green]"
        )
        raise typer.Exit()


@app.callback()
def main_callback(
    ctx: typer.Context,
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show application version and exit.",
        ),
    ] = None,
    config_path: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Optional path to configuration file.",
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
    ] = None,
) -> None:
    """Global CLI options and entry hook."""
    ctx.obj = {"config_path": config_path}


def get_service(config_path: Path | None = None) -> ConfigurationService:
    """Load configuration, using an empty configuration when no file exists."""
    try:
        return ConfigurationService.load(config_path)
    except FileNotFoundError:
        return ConfigurationService(Configuration())
    except InvalidConfigurationError as err:
        err_console.print(f"[bold red]Configuration Error:[/bold red] {err}")
        raise typer.Exit(code=1) from err


@app.command("get")
def get_config(
    ctx: typer.Context,
    key: str = typer.Argument(..., help="Key name to retrieve."),
    default: str | None = typer.Option(
        None, "--default", "-d", help="Fallback value if key is missing."
    ),
) -> None:
    """Get a configuration value by key."""
    config_path: Path | None = ctx.obj.get("config_path") if ctx.obj else None
    service = get_service(config_path)
    val = service.get_value(key, default=default)

    if val is None:
        err_console.print(f"[bold yellow]Warning:[/bold yellow] Key '{key}' not found.")
        raise typer.Exit(code=1)

    if isinstance(val, dict):
        console.print_json(json.dumps(val))
    else:
        console.print(f"[bold green]{key}:[/bold green] {val}")


@app.command("set")
def set_config(
    ctx: typer.Context,
    key: str = typer.Argument(..., help="Key name to set."),
    value: str = typer.Argument(..., help="Value to assign."),
) -> None:
    """Set a configuration value."""
    config_path: Path | None = ctx.obj.get("config_path") if ctx.obj else None
    service = get_service(config_path)

    parsed_value: ConfigurationValue = int(value) if value.isdigit() else value

    service.set_value(key, parsed_value, path=config_path)
    console.print(f"[bold green]Success:[/bold green] Set '{key}' to '{parsed_value}'.")


if __name__ == "__main__":
    main()
