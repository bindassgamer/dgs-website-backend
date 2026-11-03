import re
from decimal import Decimal

PRICE_PATTERN = re.compile(
    r"(\d[\d,]*(?:\.\d+)?)(?:\s*(cr|crore|crores|lac|lacs|lakh|lakhs)\b)?",
    re.IGNORECASE,
)
SCALES = {
    "cr": 10**7,
    "crore": 10**7,
    "crores": 10**7,
    "lac": 10**5,
    "lacs": 10**5,
    "lakh": 10**5,
    "lakhs": 10**5,
}
MAX_PRICE = Decimal(10**12)


def parse_price(text):
    """First amount in a price text as rupees, or None.

    "₹ 2.89 Cr Onwards" -> 28900000.00, "89 Lacs" -> 8900000.00,
    "₹ 75,00,000" -> 7500000.00, "Price on request" -> None.
    """
    match = PRICE_PATTERN.search(text or "")
    if match is None:
        return None
    amount = Decimal(match.group(1).replace(",", ""))
    amount *= SCALES.get((match.group(2) or "").lower(), 1)
    if amount >= MAX_PRICE:
        return None
    return amount.quantize(Decimal("0.01"))
