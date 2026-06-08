#!/usr/bin/env python3
"""
cli.py — Command-line entry point for the Binance Futures Testnet trading bot.

Usage examples:
    python cli.py --symbol BTCUSDT --side BUY  --type MARKET --quantity 0.001
    python cli.py --symbol ETHUSDT --side SELL --type LIMIT  --quantity 0.01 --price 2500
    python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 58000

Credentials are read from environment variables:
    BINANCE_API_KEY
    BINANCE_API_SECRET
Or passed explicitly via --api-key / --api-secret flags.
"""

import argparse
import os
import sys
from decimal import Decimal

from bot.client import BinanceFuturesClient
from bot.logging_config import setup_logger
from bot.orders import place_limit_order, place_market_order, place_stop_market_order
from bot.validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)

logger = setup_logger("trading_bot.cli")

SEPARATOR = "─" * 56


def _print_section(title: str) -> None:
    print(f"\n{'─'*3} {title} {'─'*(52 - len(title))}")


def _print_request_summary(args: argparse.Namespace) -> None:
    _print_section("Order Request")
    print(f"  Symbol     : {args.symbol}")
    print(f"  Side       : {args.side}")
    print(f"  Type       : {args.type}")
    print(f"  Quantity   : {args.quantity}")
    if args.price:
        print(f"  Price      : {args.price}")
    if args.stop_price:
        print(f"  Stop Price : {args.stop_price}")
    if args.type == "LIMIT":
        print(f"  TIF        : {args.time_in_force}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place orders on Binance Futures Testnet (USDT-M)",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            "  Market buy  : python cli.py -s BTCUSDT --side BUY  --type MARKET --quantity 0.001\n"
            "  Limit sell  : python cli.py -s ETHUSDT --side SELL --type LIMIT  --quantity 0.01 --price 2500\n"
            "  Stop market : python cli.py -s BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 58000\n"
        ),
    )

    # Credentials (env-var fallbacks)
    creds = parser.add_argument_group("credentials")
    creds.add_argument(
        "--api-key",
        default=os.environ.get("BINANCE_API_KEY"),
        help="Testnet API key  [env: BINANCE_API_KEY]",
    )
    creds.add_argument(
        "--api-secret",
        default=os.environ.get("BINANCE_API_SECRET"),
        help="Testnet API secret  [env: BINANCE_API_SECRET]",
    )

    # Order parameters
    order = parser.add_argument_group("order parameters")
    order.add_argument(
        "-s", "--symbol",
        required=True,
        help="Trading pair, e.g. BTCUSDT",
    )
    order.add_argument(
        "--side",
        required=True,
        choices=["BUY", "SELL"],
        type=str.upper,
        help="BUY or SELL",
    )
    order.add_argument(
        "--type",
        dest="type",
        required=True,
        choices=["MARKET", "LIMIT", "STOP_MARKET"],
        type=str.upper,
        help="Order type",
    )
    order.add_argument(
        "--quantity",
        required=True,
        help="Order quantity (base asset)",
    )
    order.add_argument(
        "--price",
        default=None,
        help="Limit price (required for LIMIT orders)",
    )
    order.add_argument(
        "--stop-price",
        dest="stop_price",
        default=None,
        help="Stop trigger price (required for STOP_MARKET orders)",
    )
    order.add_argument(
        "--time-in-force",
        dest="time_in_force",
        default="GTC",
        choices=["GTC", "IOC", "FOK"],
        help="Time-in-force for LIMIT orders (default: GTC)",
    )

    return parser


def main() -> None:
    # Avoid UnicodeEncodeError on Windows console by reconfiguring stdout/stderr to UTF-8
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = _build_parser()
    args = parser.parse_args()

    print(f"\n{'═'*56}")
    print("  Binance Futures Testnet — Trading Bot")
    print(f"{'═'*56}")

    # ── Credential check ──────────────────────────────────────────────
    if not args.api_key or not args.api_secret:
        print(
            "\n  ERROR: API credentials not provided.\n"
            "  Set BINANCE_API_KEY / BINANCE_API_SECRET env vars\n"
            "  or use --api-key / --api-secret flags.\n"
        )
        logger.error("API credentials missing — aborting.")
        sys.exit(1)

    # ── Validate inputs ───────────────────────────────────────────────
    try:
        args.symbol = validate_symbol(args.symbol)
        args.side = validate_side(args.side)
        args.type = validate_order_type(args.type)
        quantity: Decimal = validate_quantity(args.quantity)
        price: Decimal | None = validate_price(args.price, args.type)
        stop_price: Decimal | None = validate_stop_price(args.stop_price, args.type)
    except ValueError as exc:
        print(f"\n  VALIDATION ERROR: {exc}\n")
        logger.error("Validation failed: %s", exc)
        sys.exit(2)

    logger.info(
        "Order request | symbol=%s side=%s type=%s qty=%s price=%s stopPrice=%s",
        args.symbol,
        args.side,
        args.type,
        quantity,
        price,
        stop_price,
    )

    _print_request_summary(args)

    # ── Build client ──────────────────────────────────────────────────
    try:
        client = BinanceFuturesClient(
            api_key=args.api_key,
            api_secret=args.api_secret,
        )
    except ValueError as exc:
        print(f"\n  CLIENT ERROR: {exc}\n")
        logger.error("Client init failed: %s", exc)
        sys.exit(1)

    # ── Place order ───────────────────────────────────────────────────
    _print_section("Placing Order …")

    if args.type == "MARKET":
        result = place_market_order(
            client=client,
            symbol=args.symbol,
            side=args.side,
            quantity=quantity,
        )
    elif args.type == "LIMIT":
        result = place_limit_order(
            client=client,
            symbol=args.symbol,
            side=args.side,
            quantity=quantity,
            price=price,
            time_in_force=args.time_in_force,
        )
    elif args.type == "STOP_MARKET":
        result = place_stop_market_order(
            client=client,
            symbol=args.symbol,
            side=args.side,
            quantity=quantity,
            stop_price=stop_price,
        )
    else:
        # Should be unreachable thanks to argparse choices, but guard anyway
        print(f"\n  ERROR: Unsupported order type '{args.type}'\n")
        sys.exit(2)

    # ── Print result ──────────────────────────────────────────────────
    _print_section("Order Response")
    for line in result.summary_lines():
        print(line)

    print(f"\n{'═'*56}")
    if result.success:
        print(f"  ✓  Order submitted successfully!")
    else:
        print(f"  ✗  Order failed.")
    print(f"{'═'*56}\n")

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
