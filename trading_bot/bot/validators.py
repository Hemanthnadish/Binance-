"""
Input validation for trading bot CLI arguments.
All validators raise ValueError with descriptive messages on bad input.
"""

from decimal import Decimal, InvalidOperation
from typing import Optional

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


def validate_symbol(symbol: str) -> str:
    """Uppercase and basic sanity-check a trading symbol."""
    symbol = symbol.strip().upper()
    if not symbol.isalnum():
        raise ValueError(
            f"Invalid symbol '{symbol}': must contain only letters and digits (e.g. BTCUSDT)."
        )
    if len(symbol) < 3 or len(symbol) > 20:
        raise ValueError(
            f"Invalid symbol '{symbol}': length must be between 3 and 20 characters."
        )
    return symbol


def validate_side(side: str) -> str:
    """Validate order side."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(
            f"Invalid side '{side}': must be one of {sorted(VALID_SIDES)}."
        )
    return side


def validate_order_type(order_type: str) -> str:
    """Validate order type."""
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}': must be one of {sorted(VALID_ORDER_TYPES)}."
        )
    return order_type


def validate_quantity(quantity: str) -> Decimal:
    """Validate and parse quantity as a positive Decimal."""
    try:
        qty = Decimal(str(quantity))
    except InvalidOperation:
        raise ValueError(f"Invalid quantity '{quantity}': must be a numeric value.")
    if qty <= 0:
        raise ValueError(f"Invalid quantity '{quantity}': must be greater than zero.")
    return qty


def validate_price(price: Optional[str], order_type: str) -> Optional[Decimal]:
    """
    Validate price field.
    - Required for LIMIT orders.
    - Must be None / omitted for MARKET and STOP_MARKET orders.
    """
    order_type = order_type.upper()

    if order_type in ("MARKET", "STOP_MARKET"):
        if price is not None:
            raise ValueError(f"Price should not be provided for {order_type} orders.")
        return None

    if order_type == "LIMIT":
        if price is None:
            raise ValueError("Price is required for LIMIT orders.")
        try:
            p = Decimal(str(price))
        except InvalidOperation:
            raise ValueError(f"Invalid price '{price}': must be a numeric value.")
        if p <= 0:
            raise ValueError(f"Invalid price '{price}': must be greater than zero.")
        return p

    return None


def validate_stop_price(stop_price: Optional[str], order_type: str) -> Optional[Decimal]:
    """Validate stop price — required only for STOP_MARKET orders."""
    if order_type.upper() != "STOP_MARKET":
        return None
    if stop_price is None:
        raise ValueError("Stop price (--stop-price) is required for STOP_MARKET orders.")
    try:
        sp = Decimal(str(stop_price))
    except InvalidOperation:
        raise ValueError(f"Invalid stop price '{stop_price}': must be a numeric value.")
    if sp <= 0:
        raise ValueError(f"Invalid stop price '{stop_price}': must be greater than zero.")
    return sp
