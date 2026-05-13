"""
webhook/handler.py — Core logic for processing incoming TradingView signals

Expected JSON payload from TradingView OptiTrade alert box:
{
  "secret":     "YOUR_WEBHOOK_SECRET",
  "symbol":     "AAPL",
  "action":     "buy",          // buy | sell | close
  "quantity":   1,              // number of shares
  "order_type": "market",       // market | limit (optional, default market)
  "price":      150.00          // only needed if order_type = limit
}
"""
from core.config import Config
from core.logger import get_logger
from core.database import log_trade, log_webhook
from brokers.alpaca_adapter import AlpacaAdapter

logger = get_logger(__name__)
alpaca = AlpacaAdapter()

VALID_ACTIONS = {"buy", "sell", "close", "close_all"}

def process_webhook(payload: dict) -> dict:
    """
    Main webhook processor.
    Returns dict: { "success": bool, "message": str, "order": dict|None }
    """
    log_webhook(payload, "received")

    # ── 1. Kill switch check ──────────────────────────────────────────────
    if Config.KILL_SWITCH:
        msg = "Kill switch is ON — all trading halted."
        logger.warning(msg)
        log_webhook(payload, "rejected", msg)
        return {"success": False, "message": msg, "order": None}

    # ── 2. Secret validation ─────────────────────────────────────────────
    if payload.get("secret") != Config.WEBHOOK_SECRET:
        msg = "Invalid webhook secret."
        logger.warning(msg)
        log_webhook(payload, "rejected", msg)
        return {"success": False, "message": msg, "order": None}

    # ── 3. Parse fields ───────────────────────────────────────────────────
    action     = str(payload.get("action", "")).lower().strip()
    symbol     = str(payload.get("symbol", "")).upper().strip()
    quantity   = float(payload.get("quantity", 1))
    order_type = str(payload.get("order_type", "market")).lower()
    price      = float(payload.get("price", 0))

    # ── 4. Validate ───────────────────────────────────────────────────────
    if action not in VALID_ACTIONS:
        msg = f"Unknown action: '{action}'. Must be one of {VALID_ACTIONS}"
        log_webhook(payload, "error", msg)
        return {"success": False, "message": msg, "order": None}

    if not symbol and action not in {"close_all"}:
        msg = "Symbol is required."
        log_webhook(payload, "error", msg)
        return {"success": False, "message": msg, "order": None}

    if quantity <= 0:
        msg = f"Invalid quantity: {quantity}"
        log_webhook(payload, "error", msg)
        return {"success": False, "message": msg, "order": None}

    # ── 5. Risk check: max position size ─────────────────────────────────
    if quantity > Config.MAX_POSITION_SIZE:
        msg = f"Quantity {quantity} exceeds MAX_POSITION_SIZE {Config.MAX_POSITION_SIZE}"
        logger.warning(msg)
        log_webhook(payload, "rejected", msg)
        return {"success": False, "message": msg, "order": None}

    # ── 6. Execute ────────────────────────────────────────────────────────
    try:
        order_result = None

        if action == "buy":
            # For Buy-Sell flip strategy: close existing short first, then buy
            _try_close_opposite(symbol, "sell")
            if order_type == "limit" and price > 0:
                order_result = alpaca.place_limit_order(symbol, "buy", quantity, price)
            else:
                order_result = alpaca.place_market_order(symbol, "buy", quantity)

        elif action == "sell":
            # For Buy-Sell flip strategy: close existing long first, then sell
            _try_close_opposite(symbol, "buy")
            if order_type == "limit" and price > 0:
                order_result = alpaca.place_limit_order(symbol, "sell", quantity, price)
            else:
                order_result = alpaca.place_market_order(symbol, "sell", quantity)

        elif action == "close":
            order_result = alpaca.close_position(symbol)

        elif action == "close_all":
            order_result = alpaca.close_all_positions()

        alpaca_id = order_result.get("id") if order_result else None
        log_trade(symbol, action, quantity, order_type, "placed", alpaca_id)
        log_webhook(payload, "success")

        msg = f"Order placed: {action.upper()} {quantity} {symbol}"
        logger.info(msg)
        return {"success": True, "message": msg, "order": order_result}

    except Exception as e:
        msg = f"Order failed: {str(e)}"
        logger.error(msg)
        log_trade(symbol, action, quantity, order_type, "failed", message=msg)
        log_webhook(payload, "error", msg)
        return {"success": False, "message": msg, "order": None}


def _try_close_opposite(symbol: str, existing_side: str):
    """
    For flip strategies: if there's an open position on the opposite side,
    close it before opening the new one. Silently skips if no position exists.
    """
    try:
        position = alpaca.get_position(symbol)
        if position:
            qty = float(position.get("qty", 0))
            if existing_side == "sell" and qty < 0:
                logger.info(f"Flip: closing short on {symbol} before BUY")
                alpaca.close_position(symbol)
            elif existing_side == "buy" and qty > 0:
                logger.info(f"Flip: closing long on {symbol} before SELL")
                alpaca.close_position(symbol)
    except Exception as e:
        logger.warning(f"Could not check/close opposite position for {symbol}: {e}")
