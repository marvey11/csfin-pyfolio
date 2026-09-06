from decimal import Decimal


def clean_decimal(value: str) -> Decimal:
    return Decimal(value)
