"""Turn raw strings into clean, typed values."""

import re


def to_price_gbp(price_text: str | None) -> float | None:
    """'£51.77' -> 51.77. Returns None if no number is present."""
    if not price_text:
        return None
    digits = re.sub(r"[^\d.]", "", price_text)
    try:
        return float(digits)
    except ValueError:
        return None


def normalize(raw: dict) -> dict:
    """Add clean values alongside the raw ones; never replace them."""
    return {**raw, "price_gbp": to_price_gbp(raw.get("price_text"))}
