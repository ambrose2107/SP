"""
core/database.py — SQLite database for trade log
Uses a shared connection for :memory: (tests), file-based for production.
"""
import sqlite3
import os
import threading

DB_PATH = os.environ.get("DB_PATH", "trades.db")
_local = threading.local()

def get_conn():
    """
    For :memory: DBs (tests), return a shared connection per thread.
    For file-based DBs (production), open a new connection each time.
    """
    global DB_PATH
    DB_PATH = os.environ.get("DB_PATH", "trades.db")
    if DB_PATH == ":memory:":
        if not hasattr(_local, "conn") or _local.conn is None:
            _local.conn = sqlite3.connect(":memory:", check_same_thread=False)
            _local.conn.row_factory = sqlite3.Row
        return _local.conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def _close_if_not_memory(conn):
    if DB_PATH != ":memory:":
        conn.close()

def reset_memory_db():
    """Call this in test setUp to get a fresh in-memory DB."""
    if hasattr(_local, "conn") and _local.conn:
        _local.conn.close()
    _local.conn = None

def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    DEFAULT (datetime('now')),
            symbol      TEXT    NOT NULL,
            action      TEXT    NOT NULL,
            quantity    REAL    NOT NULL,
            order_type  TEXT    NOT NULL,
            status      TEXT    NOT NULL,
            alpaca_id   TEXT,
            message     TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS webhook_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    DEFAULT (datetime('now')),
            raw_payload TEXT,
            status      TEXT,
            error       TEXT
        )
    """)
    conn.commit()
    _close_if_not_memory(conn)

def log_trade(symbol, action, quantity, order_type, status, alpaca_id=None, message=None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO trades (symbol,action,quantity,order_type,status,alpaca_id,message) VALUES (?,?,?,?,?,?,?)",
        (symbol, action, quantity, order_type, status, alpaca_id, message)
    )
    conn.commit()
    _close_if_not_memory(conn)

def log_webhook(raw_payload, status, error=None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO webhook_log (raw_payload,status,error) VALUES (?,?,?)",
        (str(raw_payload), status, error)
    )
    conn.commit()
    _close_if_not_memory(conn)

def get_recent_trades(limit=50):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM trades ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    _close_if_not_memory(conn)
    return [dict(r) for r in rows]

def get_recent_webhooks(limit=20):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM webhook_log ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    _close_if_not_memory(conn)
    return [dict(r) for r in rows]
