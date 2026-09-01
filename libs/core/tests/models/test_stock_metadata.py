import pytest
from pydantic import ValidationError

from core.models import StockMetadata

# ============================================================================
# ISIN Validation Tests
# ============================================================================


def test_valid_isin_formats() -> None:
    # Standard valid ISINs
    s1 = StockMetadata(isin="DE1234567890")
    s2 = StockMetadata(isin="US0378331005")
    assert s1.isin == "DE1234567890"
    assert s2.isin == "US0378331005"


def test_isin_normalizes_lowercase_and_whitespace() -> None:
    # Should strip whitespace and convert to uppercase automatically
    s = StockMetadata(isin="  de1234567890  ")
    assert s.isin == "DE1234567890"


@pytest.mark.parametrize(
    "invalid_isin",
    [
        "DE123456789",  # Too short (11 chars)
        "DE12345678901",  # Too long (13 chars)
        "121234567890",  # Country prefix numbers instead of letters
        "DE123456789X",  # Check digit must be numeric
        "DE-123456789",  # Invalid hyphens
    ],
)
def test_invalid_isin_raises_validation_error(invalid_isin: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        StockMetadata(isin=invalid_isin)
    assert "Invalid ISIN format" in str(exc_info.value)


# ============================================================================
# Country Code Validation Tests
# ============================================================================


def test_valid_country_code() -> None:
    s = StockMetadata(isin="DE1234567890", country_code="de")  # Lowercase input
    assert s.country_code == "DE"  # Converted to uppercase


def test_country_code_optional() -> None:
    s = StockMetadata(isin="DE1234567890", country_code=None)
    assert s.country_code is None


@pytest.mark.parametrize("invalid_cc", ["D", "DEU", "12", "D!"])
def test_invalid_country_code_raises_validation_error(invalid_cc: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        StockMetadata(isin="DE1234567890", country_code=invalid_cc)
    assert "Invalid country code" in str(exc_info.value)


# ============================================================================
# Currency Code Validation Tests
# ============================================================================


def test_valid_currency_code() -> None:
    s = StockMetadata(isin="DE1234567890", currency_code="eur")  # Lowercase input
    assert s.currency_code == "EUR"  # Converted to uppercase


def test_currency_code_optional() -> None:
    s = StockMetadata(isin="DE1234567890", currency_code=None)
    assert s.currency_code is None


@pytest.mark.parametrize("invalid_curr", ["EU", "EURO", "123", "EU$"])
def test_invalid_currency_code_raises_validation_error(invalid_curr: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        StockMetadata(isin="DE1234567890", currency_code=invalid_curr)
    assert "Invalid currency code" in str(exc_info.value)
