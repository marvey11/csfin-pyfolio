from __future__ import annotations

from typing import TYPE_CHECKING

from config import Configuration

if TYPE_CHECKING:
    from pytest import MonkeyPatch


def test_parse_returns_configuration_instance() -> None:
    """Verify that Configuration.parse() returns an initialized instance."""
    config = Configuration.parse()

    assert isinstance(config, Configuration)


def test_parse_with_env_vars(monkeypatch: MonkeyPatch) -> None:
    """
    Example test using pytest's built-in monkeypatch fixture to mock environment
    variables.
    """
    # Set fake environment variables if your parse method eventually reads from
    # os.environ
    monkeypatch.setenv("APP_ENV", "test")

    config = Configuration.parse()

    # Add assertions matching your implementation
    assert isinstance(config, Configuration)
