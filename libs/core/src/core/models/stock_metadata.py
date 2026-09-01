import re
from typing import Self

from pydantic import BaseModel, field_validator

ISIN_REGEX = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
COUNTRY_REGEX = re.compile(r"^[A-Z]{2}$")
CURRENCY_REGEX = re.compile(r"^[A-Z]{3}$")


class StockMetadata(BaseModel):
    isin: str
    name: str | None = None
    country_code: str | None = None
    currency_code: str | None = None

    @field_validator("isin")
    @classmethod
    def validate_isin(cls, v: str) -> str:
        v = v.strip().upper()
        if not ISIN_REGEX.match(v):
            raise ValueError(
                f"Invalid ISIN format: '{v}'. "
                "Must be 12 uppercase alphanumeric characters."
            )
        return v

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().upper()
        if not COUNTRY_REGEX.match(v):
            raise ValueError(
                f"Invalid country code: '{v}'. Must be a 2-letter ISO code."
            )
        return v

    @field_validator("currency_code")
    @classmethod
    def validate_currency_code(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().upper()
        if not CURRENCY_REGEX.match(v):
            raise ValueError(
                f"Invalid currency code: '{v}'. Must be a 3-letter ISO code."
            )
        return v

    def update(self, other: Self) -> None:
        """Updates the instance attributes in-place."""
        for key, value in other.model_dump(exclude_none=True).items():
            if key != "isin":
                setattr(self, key, value)
