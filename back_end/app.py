from flask import Flask, render_template, Response, abort, send_from_directory
import logging
from pathlib import Path

# Import configuration
from .config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG

# Import services and utilities
from .services.scheduler import setup_scheduler
from .utils.helpers import cleanup_duplicate_csv_files

# Import API blueprint
from .api.routes import api

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
    
    print("🚀 Starting Stock Dashboard...")
    
    # Clean up duplicate CSV files on startup
    cleanup_result = cleanup_duplicate_csv_files()
    if cleanup_result['deleted'] > 0:
        print(f"🧹 Cleaned up {cleanup_result['deleted']} duplicate CSV files")
    
    # Use variables for host and port
    host = FLASK_HOST
    port = FLASK_PORT

    print("📊 Dashboard available at:")
    print(f"   • Modern UI: http://localhost:{port}/")
    print(f"   • API Health: http://localhost:{port}/api/health")
    print("")
    print("📂 CSV Database Management:")
    print(f"   • List Databases: http://localhost:{port}/api/database/list")
    print(f"   • Save to DB: http://localhost:{port}/api/database/save/AAPL")
    print(f"   • Load from DB: http://localhost:{port}/api/database/load/AAPL")
    print(f"   • Update All: http://localhost:{port}/api/database/update-all")
    print("")
    print("📈 Advanced Analytics:")
    print(f"   • Market Correlation: http://localhost:{port}/api/market/correlation")
    print(f"   • Market Events: http://localhost:{port}/api/market/events")
    print(f"   • Manual Cleanup: http://localhost:{port}/api/cleanup")
    print("")
    
    # Setup scheduler if configured
    from .config import AUTO_DOWNLOAD_ENABLED
    if AUTO_DOWNLOAD_ENABLED:
        setup_scheduler()
        print("⏰ Automated data collection enabled")
    else:
        print("⚠️  Automated data collection disabled (API key not configured)")
    
    return app 