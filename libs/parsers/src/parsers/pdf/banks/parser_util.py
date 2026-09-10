from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, overload

from codescape.util.number_parse import clean_decimal

if TYPE_CHECKING:
    from decimal import Decimal

T = TypeVar("T")


@overload
def get_parsed_decimal(
    repository: dict[str, str | None],
    key: str,
    default: None = None,
) -> Decimal | None: ...


@overload
def get_parsed_decimal[T](
    repository: dict[str, str | None],
    key: str,
    default: T,
) -> Decimal | T: ...


def get_parsed_decimal[T](
    repository: dict[str, str | None],
    key: str,
    default: T | None = None,
) -> Decimal | T | None:
    value = repository.get(key)
    if value is None or value == "":
        return default
    return clean_decimal(value)
