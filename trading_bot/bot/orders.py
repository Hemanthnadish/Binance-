"""
Order placement logic.

Translates validated user intent into Binance API calls and returns
a structured OrderResult dataclass for clean downstream consumption.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, Optional

from .client import BinanceFuturesClient
from .logging_config import setup_logger

logger = setup_logger("trading_bot.orders")


@dataclass
class OrderResult:
    """Normalised representation of a Binance order response."""

    success: bool
    order_id: Optional[int] = None
    client_order_id: Optional[str] = None
    symbol: Optional[str] = None
    side: Optional[str] = None
    order_type: Optional[str] = None
    status: Optional[str] = None
    price: Optional[str] = None
    avg_price: Optional[str] = None
    orig_qty: Optional[str] = None
    executed_qty: Optional[str] = None
    time_in_force: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def summary_lines(self) -> list[str]:
        """Return human-readable summary lines for CLI output."""
        if not self.success:
            return [f"  ✗ Order FAILED: {self.error}"]
        lines = [
            f"  Order ID      : {self.order_id}",
            f"  Client OID    : {self.client_order_id}",
            f"  Symbol        : {self.symbol}",
            f"  Side          : {self.side}",
            f"  Type          : {self.order_type}",
            f"  Status        : {self.status}",
        ]
        if self.price and self.price != "0":
            lines.append(f"  Price         : {self.price}")
        if self.avg_price and self.avg_price != "0":
            lines.append(f"  Avg Fill Price: {self.avg_price}")
        lines += [
            f"  Orig Qty      : {self.orig_qty}",
            f"  Executed Qty  : {self.executed_qty}",
        ]
        if self.time_in_force:
            lines.append(f"  Time-In-Force : {self.time_in_force}")
        return lines


def _parse_response(raw: Dict[str, Any]) -> OrderResult:
    """Map a raw Binance order response dict to an OrderResult."""
    return OrderResult(
        success=True,
        order_id=raw.get("orderId"),
        client_order_id=raw.get("clientOrderId"),
        symbol=raw.get("symbol"),
        side=raw.get("side"),
        order_type=raw.get("type"),
        status=raw.get("status"),
        price=raw.get("price"),
        avg_price=raw.get("avgPrice"),
        orig_qty=raw.get("origQty"),
        executed_qty=raw.get("executedQty"),
        time_in_force=raw.get("timeInForce"),
        raw=raw,
    )


def place_market_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: Decimal,
) -> OrderResult:
    """
    Place a MARKET order.

    Parameters
    ----------
    client   : authenticated BinanceFuturesClient instance
    symbol   : e.g. "BTCUSDT"
    side     : "BUY" or "SELL"
    quantity : order size
    """
    logger.info(
        "Placing MARKET %s %s qty=%s",
        side,
        symbol,
        quantity,
    )
    params = dict(
        symbol=symbol,
        side=side,
        type="MARKET",
        quantity=str(quantity),
    )
    try:
        raw = client.place_order(**params)
        result = _parse_response(raw)
        logger.info(
            "MARKET order placed successfully | orderId=%s status=%s executedQty=%s",
            result.order_id,
            result.status,
            result.executed_qty,
        )
        return result
    except Exception as exc:
        logger.error("Failed to place MARKET order: %s", exc)
        return OrderResult(success=False, error=str(exc))


def place_limit_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: Decimal,
    price: Decimal,
    time_in_force: str = "GTC",
) -> OrderResult:
    """
    Place a LIMIT order.

    Parameters
    ----------
    client        : authenticated BinanceFuturesClient instance
    symbol        : e.g. "BTCUSDT"
    side          : "BUY" or "SELL"
    quantity      : order size
    price         : limit price
    time_in_force : GTC (default) | IOC | FOK
    """
    logger.info(
        "Placing LIMIT %s %s qty=%s price=%s tif=%s",
        side,
        symbol,
        quantity,
        price,
        time_in_force,
    )
    params = dict(
        symbol=symbol,
        side=side,
        type="LIMIT",
        quantity=str(quantity),
        price=str(price),
        timeInForce=time_in_force,
    )
    try:
        raw = client.place_order(**params)
        result = _parse_response(raw)
        logger.info(
            "LIMIT order placed successfully | orderId=%s status=%s price=%s",
            result.order_id,
            result.status,
            result.price,
        )
        return result
    except Exception as exc:
        logger.error("Failed to place LIMIT order: %s", exc)
        return OrderResult(success=False, error=str(exc))


def place_stop_market_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: Decimal,
    stop_price: Decimal,
) -> OrderResult:
    """
    Place a STOP_MARKET order (bonus order type).

    Triggers a market order once the stop price is reached.

    Parameters
    ----------
    client     : authenticated BinanceFuturesClient instance
    symbol     : e.g. "BTCUSDT"
    side       : "BUY" or "SELL"
    quantity   : order size
    stop_price : price that triggers the market order
    """
    logger.info(
        "Placing STOP_MARKET %s %s qty=%s stopPrice=%s",
        side,
        symbol,
        quantity,
        stop_price,
    )
    params = dict(
        symbol=symbol,
        side=side,
        type="STOP_MARKET",
        quantity=str(quantity),
        stopPrice=str(stop_price),
    )
    try:
        raw = client.place_order(**params)
        result = _parse_response(raw)
        logger.info(
            "STOP_MARKET order placed successfully | orderId=%s status=%s",
            result.order_id,
            result.status,
        )
        return result
    except Exception as exc:
        logger.error("Failed to place STOP_MARKET order: %s", exc)
        return OrderResult(success=False, error=str(exc))
