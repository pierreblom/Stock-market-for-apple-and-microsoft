import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# API Configuration
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', None) # We will now require this to be in the .env file
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', None) # Add Alpha Vantage key
API_TIMEOUT = int(os.getenv('API_TIMEOUT_SECONDS', 15))
API_QUICK_TIMEOUT = int(os.getenv('API_QUICK_TIMEOUT_SECONDS', 10))
HISTORICAL_DATA_LIMIT = int(os.getenv('HISTORICAL_DATA_LIMIT', 121))

# Server Configuration
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 8001))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Scheduling Configuration (Amsterdam timezone - CET/CEST)
DAILY_UPDATE_HOUR = int(os.getenv('DAILY_UPDATE_HOUR', 19))  # 7 PM CET (after European markets close)
DAILY_UPDATE_MINUTE = int(os.getenv('DAILY_UPDATE_MINUTE', 0))  # Top of the hour
AUTO_DOWNLOAD_ENABLED = os.getenv('AUTO_DOWNLOAD_ENABLED', 'True').lower() == 'true'

# Dutch and European stocks for Amsterdam user
AUTO_DOWNLOAD_SYMBOLS = [
    'AAPL',   # Using Apple as a test stock since it's available on the free plan
]

# Directories
EXPORT_DIR = Path("data_exports")
EXPORT_DIR.mkdir(exist_ok=True)