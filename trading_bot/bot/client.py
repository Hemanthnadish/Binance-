"""
Binance Futures Testnet REST API client.

Handles:
- HMAC-SHA256 request signing
- Timestamp synchronisation
- HTTP session management with retries
- Structured logging of every request / response / error
"""

import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .logging_config import setup_logger

TESTNET_BASE_URL = "https://testnet.binancefuture.com"
API_VERSION = "/fapi/v1"

logger = setup_logger("trading_bot.client")


def _build_session(retries: int = 3) -> requests.Session:
    """Return a requests Session with automatic retries on transient errors."""
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST", "DELETE"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class BinanceFuturesClient:
    """
    Binance Futures Testnet REST API client.

    Parameters
    ----------
    api_key : str
        Your testnet API key.
    api_secret : str
        Your testnet API secret.
    base_url : str
        Override the default testnet base URL if needed.
    timeout : int
        Request timeout in seconds (default 10).
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = TESTNET_BASE_URL,
        timeout: int = 10,
    ) -> None:
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret must be non-empty strings.")
        self._api_key = api_key
        self._api_secret = api_secret
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = _build_session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.debug("BinanceFuturesClient initialised. Base URL: %s", self._base_url)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Append HMAC-SHA256 signature to a parameter dict."""
        query_string = urlencode(params)
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    @staticmethod
    def _timestamp() -> int:
        return int(time.time() * 1000)

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
    ) -> Dict[str, Any]:
        """
        Generic HTTP request helper.

        Raises
        ------
        requests.exceptions.RequestException
            On network-level errors.
        RuntimeError
            When Binance returns a non-2xx response (carries the API error message).
        """
        params = params or {}
        if signed:
            params["timestamp"] = self._timestamp()
            params = self._sign(params)

        url = f"{self._base_url}{API_VERSION}{endpoint}"
        logger.debug(
            "REQUEST  %s %s | params: %s",
            method.upper(),
            url,
            json.dumps({k: v for k, v in params.items() if k != "signature"}),
        )

        try:
            if method.upper() == "GET":
                response = self._session.get(url, params=params, timeout=self._timeout)
            elif method.upper() == "POST":
                response = self._session.post(url, data=params, timeout=self._timeout)
            elif method.upper() == "DELETE":
                response = self._session.delete(url, params=params, timeout=self._timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network connection error: %s", exc)
            raise
        except requests.exceptions.Timeout as exc:
            logger.error("Request timed out after %ds: %s", self._timeout, exc)
            raise
        except requests.exceptions.RequestException as exc:
            logger.error("Unexpected request error: %s", exc)
            raise

        logger.debug(
            "RESPONSE %s %s | status: %d | body: %s",
            method.upper(),
            url,
            response.status_code,
            response.text[:2000],  # cap log size
        )

        if not response.ok:
            try:
                err_body = response.json()
                msg = err_body.get("msg", response.text)
                code = err_body.get("code", response.status_code)
            except ValueError:
                msg = response.text
                code = response.status_code
            logger.error("API error %s: %s", code, msg)
            raise RuntimeError(f"Binance API error {code}: {msg}")

        return response.json()

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_server_time(self) -> int:
        """Return Binance server time in milliseconds."""
        data = self._request("GET", "/time")
        return data["serverTime"]

    def get_exchange_info(self) -> Dict[str, Any]:
        """Return exchange info (symbols, filters, etc.)."""
        return self._request("GET", "/exchangeInfo")

    def get_account(self) -> Dict[str, Any]:
        """Return futures account details."""
        return self._request("GET", "/account", signed=True)

    def place_order(self, **kwargs) -> Dict[str, Any]:
        """
        Place a new order on Binance USDT-M Futures Testnet.

        Accepts any keyword arguments that map directly to Binance order
        parameters (symbol, side, type, quantity, price, timeInForce, etc.).
        """
        return self._request("POST", "/order", params=dict(kwargs), signed=True)

    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an open order by orderId."""
        params = {"symbol": symbol, "orderId": order_id}
        return self._request("DELETE", "/order", params=params, signed=True)

    def get_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Query status of a specific order."""
        params = {"symbol": symbol, "orderId": order_id}
        return self._request("GET", "/order", params=params, signed=True)
