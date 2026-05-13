"""
brokers/alpaca_adapter.py — Alpaca API wrapper
Handles BUY, SELL, close position, get positions
"""
import requests
import os
from core.logger import get_logger
from core.config import Config

logger = get_logger(__name__)

class AlpacaAdapter:
    def __init__(self):
        self.api_key    = Config.ALPACA_API_KEY
        self.secret_key = Config.ALPACA_SECRET_KEY
        self.base_url   = Config.ALPACA_BASE_URL
        self.headers = {
            "APCA-API-KEY-ID":     self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
            "Content-Type":        "application/json"
        }

    def _request(self, method, endpoint, payload=None):
        url = f"{self.base_url}{endpoint}"
        try:
            resp = requests.request(method, url, headers=self.headers, json=payload, timeout=10)
            resp.raise_for_status()
            return resp.json() if resp.text else {}
        except requests.exceptions.HTTPError as e:
            logger.error(f"Alpaca HTTP error: {e} | Response: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Alpaca request error: {e}")
            raise

    def get_account(self):
        return self._request("GET", "/v2/account")

    def get_positions(self):
        return self._request("GET", "/v2/positions")

    def get_position(self, symbol):
        try:
            return self._request("GET", f"/v2/positions/{symbol}")
        except:
            return None

    def place_market_order(self, symbol: str, side: str, qty: float):
        """Place a market order. side = 'buy' or 'sell'"""
        payload = {
            "symbol":        symbol.upper(),
            "qty":           str(qty),
            "side":          side.lower(),
            "type":          "market",
            "time_in_force": "day"
        }
        logger.info(f"Placing {side.upper()} {qty} {symbol} @ MARKET")
        return self._request("POST", "/v2/orders", payload)

    def place_limit_order(self, symbol: str, side: str, qty: float, limit_price: float):
        """Place a limit order."""
        payload = {
            "symbol":        symbol.upper(),
            "qty":           str(qty),
            "side":          side.lower(),
            "type":          "limit",
            "limit_price":   str(round(limit_price, 2)),
            "time_in_force": "day"
        }
        logger.info(f"Placing {side.upper()} {qty} {symbol} @ LIMIT {limit_price}")
        return self._request("POST", "/v2/orders", payload)

    def close_position(self, symbol: str):
        """Close entire position for a symbol."""
        logger.info(f"Closing position for {symbol}")
        try:
            return self._request("DELETE", f"/v2/positions/{symbol}")
        except Exception as e:
            logger.warning(f"Could not close position for {symbol}: {e}")
            return None

    def close_all_positions(self):
        """Emergency — close everything."""
        logger.warning("CLOSING ALL POSITIONS")
        return self._request("DELETE", "/v2/positions")

    def cancel_all_orders(self):
        """Cancel all open orders."""
        logger.info("Cancelling all open orders")
        return self._request("DELETE", "/v2/orders")

    def get_open_orders(self):
        return self._request("GET", "/v2/orders?status=open")

