from decimal import ROUND_HALF_UP, Decimal

MONEY_PLACES = Decimal("0.01")


def as_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)
