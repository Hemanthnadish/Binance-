# 🤖 Binance Futures Testnet Trading Bot

<div align="center">

A clean, production-structured **Python CLI** for placing orders on the **Binance USDT-M Futures Testnet**.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Binance](https://img.shields.io/badge/Binance-Futures%20Testnet-F0B90B?style=for-the-badge&logo=binance&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

</div>

---

## ✨ Features

| Capability | Details |
|---|---|
| 📦 Order Types | `MARKET`, `LIMIT`, `STOP_MARKET` |
| ↔️ Sides | `BUY`, `SELL` |
| 🖥️ CLI | `argparse` with full validation & help text |
| 📝 Logging | Dual handler — verbose file log + concise console output |
| 🛡️ Error Handling | Validation errors, API errors, network failures |
| 🏗️ Architecture | Separate `client`, `orders`, `validators`, `logging_config` layers |

---

## 📂 Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py           # Binance REST API wrapper (signing, retries, logging)
│   ├── orders.py           # Order placement logic + OrderResult dataclass
│   ├── validators.py       # Input validation (raises ValueError on bad input)
│   └── logging_config.py   # Dual-handler logger setup
├── cli.py                  # CLI entry point (argparse)
├── logs/
│   └── trading_bot_YYYYMMDD.log   # Auto-created at runtime
├── README.md
└── requirements.txt
```

---

## 🚀 Setup

### 1. Get Testnet Credentials

1. Visit [testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in with your **GitHub account**
3. Navigate to **API Key** → generate a new key pair
4. Copy your `API Key` and `Secret Key`

---

### 2. Install Dependencies

```bash
# Python 3.10+ recommended
python -m venv .venv

# Activate the virtual environment:
# macOS / Linux:
source .venv/bin/activate

# Windows (PowerShell):
.venv\Scripts\activate

pip install -r requirements.txt
```

---

### 3. Set API Credentials

**Option A — Environment Variables (Recommended)**

```bash
# Linux / macOS
export BINANCE_API_KEY="your_testnet_api_key"
export BINANCE_API_SECRET="your_testnet_api_secret"

# Windows PowerShell
$env:BINANCE_API_KEY="your_testnet_api_key"
$env:BINANCE_API_SECRET="your_testnet_api_secret"
```

**Option B — CLI Flags**

```bash
python cli.py --api-key YOUR_KEY --api-secret YOUR_SECRET ...
```

---

## ▶️ Usage

### Show Help

```bash
python cli.py --help
```

---

### 📈 MARKET Order

```bash
# Buy 0.001 BTC at market price
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Sell 0.01 ETH at market price
python cli.py --symbol ETHUSDT --side SELL --type MARKET --quantity 0.01
```

---

### 📊 LIMIT Order

```bash
# Sell 0.05 ETH with a limit at 2550 USDT (Good Till Cancelled)
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.05 --price 2550

# Buy 0.002 BTC at 41000 — Fill Or Kill
python cli.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.002 --price 41000 --time-in-force FOK
```

---

### 🛑 STOP_MARKET Order

```bash
# Trigger a market sell if BTC drops to 58000
python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 58000
```

---

## 🖨️ Example Output

```
════════════════════════════════════════════════════════
  Binance Futures Testnet — Trading Bot
════════════════════════════════════════════════════════

─── Order Request ────────────────────────────────────
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.001

─── Placing Order … ──────────────────────────────────

─── Order Response ───────────────────────────────────
  Order ID      : 4028441504
  Client OID    : web_rA8nX2pKzT9qL7mF
  Symbol        : BTCUSDT
  Side          : BUY
  Type          : MARKET
  Status        : FILLED
  Avg Fill Price: 43218.50
  Orig Qty      : 0.001
  Executed Qty  : 0.001
  Time-In-Force : GTC

════════════════════════════════════════════════════════
  ✓  Order submitted successfully!
════════════════════════════════════════════════════════
```

---

## 📋 CLI Reference

| Flag | Short | Required | Description |
|---|---|---|---|
| `--symbol` | `-s` | ✅ | Trading pair (e.g. `BTCUSDT`) |
| `--side` | — | ✅ | `BUY` or `SELL` |
| `--type` | — | ✅ | `MARKET`, `LIMIT`, or `STOP_MARKET` |
| `--quantity` | — | ✅ | Order quantity (base asset) |
| `--price` | — | For LIMIT | Limit price |
| `--stop-price` | — | For STOP_MARKET | Stop trigger price |
| `--time-in-force` | — | ❌ | `GTC` *(default)*, `IOC`, or `FOK` |
| `--api-key` | — | ❌ | Testnet API key (or use env var) |
| `--api-secret` | — | ❌ | Testnet API secret (or use env var) |

---

## 📝 Logging

Log files are automatically created in the `logs/` directory as `trading_bot_YYYYMMDD.log`.

| Handler | Level | Output |
|---|---|---|
| **File** | `DEBUG` | Full request URLs, params (no signature), raw responses, all errors |
| **Console** | `INFO` | Clean, human-readable status messages only |

---

## 🛡️ Validation & Error Handling

| Scenario | Behaviour |
|---|---|
| Missing `--price` for LIMIT | Validation error, exit code `2` |
| Non-numeric quantity / price | Validation error, exit code `2` |
| Missing API credentials | Clear error message, exit code `1` |
| Binance API error (e.g. bad symbol) | `RuntimeError` caught, logged, printed, exit code `1` |
| Network timeout / connection refused | `requests` exception caught, logged, printed, exit code `1` |

---

## ⚙️ Assumptions

- Testnet base URL is hard-coded as `https://testnet.binancefuture.com`  
  *(overridable via `BinanceFuturesClient(base_url=...)`)*
- Default position side is `BOTH` (one-way mode) — hedge mode users need to pass `positionSide` manually
- `timeInForce` defaults to `GTC` for LIMIT orders; can be overridden with `--time-in-force`
- All quantities / prices are passed as strings to preserve decimal precision *(Binance requires this)*

---

## 📦 Requirements

```
requests>=2.31.0
urllib3>=2.0.0
```

> Python standard library only otherwise — no extra dependencies needed.

---

## 📄 License

This project is licensed under the **MIT License**.

---

<div align="center">
  Made with ❤️ for the <strong>Binance Futures Testnet</strong>
</div>
