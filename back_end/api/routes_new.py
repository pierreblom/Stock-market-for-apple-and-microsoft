"""
Main API routes file that registers all domain-specific blueprints.
"""

from flask import Blueprint

# Import all route blueprints
from .health_routes import health_bp
from .stock_routes import stock_bp
from .market_routes import market_bp
from .database_routes import database_bp
from .automation_routes import automation_bp
from .tracking_routes import tracking_bp
from .docs_routes import docs_bp

# Create main API blueprint
api = Blueprint('api', __name__)

# Register all blueprints
api.register_blueprint(health_bp)
api.register_blueprint(stock_bp)
api.register_blueprint(market_bp)
api.register_blueprint(database_bp)
api.register_blueprint(automation_bp)
api.register_blueprint(tracking_bp)
api.register_blueprint(docs_bp, url_prefix='/docs') 