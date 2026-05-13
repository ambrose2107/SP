"""
dashboard/routes.py — Web dashboard blueprint
"""
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from core.database import get_recent_trades, get_recent_webhooks
from core.config import Config
from brokers.alpaca_adapter import AlpacaAdapter
from core.logger import get_logger
import os

logger = get_logger(__name__)
dashboard_bp = Blueprint("dashboard", __name__)
alpaca = AlpacaAdapter()

@dashboard_bp.route("/", methods=["GET"])
def index():
    if not session.get("logged_in"):
        return redirect(url_for("dashboard.login"))
    return render_template("dashboard.html")

@dashboard_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == Config.DASHBOARD_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("dashboard.index"))
        error = "Wrong password"
    return render_template("login.html", error=error)

@dashboard_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("dashboard.login"))

@dashboard_bp.route("/api/account")
def api_account():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    try:
        account = alpaca.get_account()
        positions = alpaca.get_positions()
        return jsonify({"account": account, "positions": positions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route("/api/trades")
def api_trades():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(get_recent_trades(50))

@dashboard_bp.route("/api/webhooks")
def api_webhooks():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(get_recent_webhooks(20))

@dashboard_bp.route("/api/close_all", methods=["POST"])
def api_close_all():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    try:
        result = alpaca.close_all_positions()
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@dashboard_bp.route("/api/kill_switch", methods=["POST"])
def api_kill_switch():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    # Toggle kill switch via env (runtime toggle stored in file)
    state = request.json.get("enabled", True)
    # Write to a flag file for runtime use
    with open(".kill_switch", "w") as f:
        f.write("1" if state else "0")
    return jsonify({"success": True, "kill_switch": state})
