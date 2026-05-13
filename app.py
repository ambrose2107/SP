"""
Flask app factory — registers all routes
"""
from flask import Flask
from core.database import init_db
from core.logger import get_logger
from webhook.routes import webhook_bp
from dashboard.routes import dashboard_bp

logger = get_logger(__name__)

def create_app():
    app = Flask(__name__, template_folder="dashboard/templates", static_folder="dashboard/static")

    # Load config
    from core.config import Config
    app.config.from_object(Config)

    # Init DB
    init_db()

    # Register blueprints
    app.register_blueprint(webhook_bp)
    app.register_blueprint(dashboard_bp)

    logger.info("App created and routes registered.")
    return app
