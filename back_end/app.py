from flask import Flask, render_template, Response, abort, send_from_directory
from pathlib import Path

# Import configuration
from .config import config

# Import services and utilities
from .services.scheduler import setup_scheduler
from .utils.helpers import cleanup_duplicate_csv_files
from .utils.logger import get_logger

# Import API blueprint (new modular structure)
from .api.routes_new import api

# Create Flask app
app = Flask(__name__,
            static_folder='../front_end',
            static_url_path='',
            template_folder='../front_end')

# Register API blueprint
app.register_blueprint(api, url_prefix='/api')


@app.route('/')
def dashboard():
    """Main dashboard page - serves consolidated frontend"""
    return render_template('dashboard.html')


def create_app():
    """Application factory function"""
    
    logger = get_logger(__name__)
    logger.info("🚀 Starting Stock Dashboard...")
    
    # Clean up duplicate CSV files on startup
    cleanup_result = cleanup_duplicate_csv_files()
    if cleanup_result['deleted'] > 0:
        logger.info(f"🧹 Cleaned up {cleanup_result['deleted']} duplicate CSV files")
    
    # Use configuration
    host = config.server.host
    port = config.server.port

    logger.info("📊 Dashboard available at:")
    logger.info(f"   • Modern UI: http://localhost:{port}/")
    logger.info(f"   • API Health: http://localhost:{port}/api/health")
    logger.info("")
    logger.info("📂 CSV Database Management:")
    logger.info(f"   • List Databases: http://localhost:{port}/api/database/list")
    logger.info(f"   • Save to DB: http://localhost:{port}/api/database/save/NVDA")
    logger.info(f"   • Load from DB: http://localhost:{port}/api/database/load/NVDA")
    logger.info(f"   • Update All: http://localhost:{port}/api/database/update-all")
    logger.info("")
    logger.info("📈 Advanced Analytics:")
    logger.info(f"   • Market Correlation: http://localhost:{port}/api/market/correlation")
    logger.info(f"   • Market Events: http://localhost:{port}/api/market/events")
    logger.info(f"   • Manual Cleanup: http://localhost:{port}/api/cleanup")
    logger.info("")
    
    # Setup scheduler if configured
    if config.scheduling.auto_download_enabled:
        setup_scheduler()
        logger.info("⏰ Automated data collection enabled")
    else:
        logger.warning("⚠️  Automated data collection disabled (API key not configured)")
    
    return app 