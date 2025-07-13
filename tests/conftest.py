"""
Pytest configuration and fixtures for the stock market dashboard tests.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from back_end.app import create_app
from back_end.config import Config


@pytest.fixture(scope="session")
def app():
    """Create and configure a new app instance for each test session."""
    # Create a temporary directory for test data
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set environment variables for testing
        os.environ.update({
            'FINNHUB_API_KEY': 'test_finnhub_key',
            'ALPHA_VANTAGE_API_KEY': 'test_alpha_key',
            'FLASK_DEBUG': 'False',
            'FLASK_HOST': 'localhost',
            'FLASK_PORT': '8001',
            'EXPORT_DIR': temp_dir,
            'LOG_LEVEL': 'DEBUG',
            'LOG_FILE_ENABLED': 'False',
            'LOG_CONSOLE_ENABLED': 'True'
        })
        
        app = create_app()
        app.config['TESTING'] = True
        
        yield app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test runner for the app's Click commands."""
    return app.test_cli_runner()


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    with patch('back_end.config.config') as mock_config:
        # Mock API configuration
        mock_config.api.finnhub_api_key = 'test_finnhub_key'
        mock_config.api.alpha_vantage_api_key = 'test_alpha_key'
        mock_config.api.timeout = 15
        mock_config.api.quick_timeout = 10
        mock_config.api.historical_data_limit = 121
        
        # Mock server configuration
        mock_config.server.host = 'localhost'
        mock_config.server.port = 8001
        mock_config.server.debug = False
        
        # Mock scheduling configuration
        mock_config.scheduling.daily_update_hour = 18
        mock_config.scheduling.daily_update_minute = 0
        mock_config.scheduling.auto_download_enabled = True
        mock_config.scheduling.auto_download_symbols = ['NVDA', 'MSFT']
        
        # Mock logging configuration
        mock_config.logging.level = 'DEBUG'
        mock_config.logging.format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        mock_config.logging.file_enabled = False
        mock_config.logging.console_enabled = True
        
        # Mock export directory
        mock_config.export_dir = Path(tempfile.mkdtemp())
        
        yield mock_config


@pytest.fixture
def mock_fetcher():
    """Mock market data fetcher for testing."""
    with patch('back_end.models.data_fetcher.MarketDataFetcher') as mock_fetcher:
        mock_instance = Mock()
        
        # Mock current data response
        mock_instance.get_current_data.return_value = {
            'success': True,
            'data': {
                'symbol': 'AAPL',
                'price': 150.0,
                'open': 148.0,
                'high': 152.0,
                'low': 147.0,
                'previous_close': 149.0,
                'change': 1.0,
                'change_percent': 0.67,
                'timestamp': '2023-01-01 12:00:00'
            },
            'message': 'Successfully fetched current data from Finnhub for AAPL'
        }
        
        # Mock historical data response
        mock_instance.get_historical_data.return_value = {
            'success': True,
            'data': [
                {
                    'date': '2023-01-01',
                    'open': 148.0,
                    'high': 152.0,
                    'low': 147.0,
                    'close': 150.0,
                    'volume': 1000000
                },
                {
                    'date': '2023-01-02',
                    'open': 150.0,
                    'high': 155.0,
                    'low': 149.0,
                    'close': 153.0,
                    'volume': 1100000
                }
            ],
            'message': 'Successfully fetched 2 records from Alpha Vantage for AAPL'
        }
        
        mock_fetcher.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_stock_data():
    """Sample stock data for testing."""
    return [
        {
            'date': '2023-01-01',
            'open': 148.0,
            'high': 152.0,
            'low': 147.0,
            'close': 150.0,
            'volume': 1000000
        },
        {
            'date': '2023-01-02',
            'open': 150.0,
            'high': 155.0,
            'low': 149.0,
            'close': 153.0,
            'volume': 1100000
        },
        {
            'date': '2023-01-03',
            'open': 153.0,
            'high': 158.0,
            'low': 152.0,
            'close': 156.0,
            'volume': 1200000
        }
    ]


@pytest.fixture
def sample_current_data():
    """Sample current stock data for testing."""
    return {
        'symbol': 'NVDA',
        'price': 165.0,
        'open': 163.0,
        'high': 167.0,
        'low': 162.0,
        'previous_close': 164.0,
        'change': 1.0,
        'change_percent': 0.61,
        'timestamp': '2023-01-01 12:00:00'
    }


@pytest.fixture
def mock_database_operations():
    """Mock database operations for testing."""
    with patch('back_end.models.database.save_to_database_csv') as mock_save, \
         patch('back_end.models.database.load_from_database_csv') as mock_load:
        
        # Mock save operation
        mock_save.return_value = {
            'success': True,
            'filename': 'AAPL_database.csv',
            'filepath': '/tmp/AAPL_database.csv',
            'records': 3,
            'total_records': 3,
            'message': 'Created new database: 3 records',
            'updated': True
        }
        
        # Mock load operation
        mock_load.return_value = {
            'success': True,
            'data': [
                {
                    'date': '2023-01-01',
                    'open': 148.0,
                    'high': 152.0,
                    'low': 147.0,
                    'close': 150.0,
                    'volume': 1000000
                },
                {
                    'date': '2023-01-02',
                    'open': 150.0,
                    'high': 155.0,
                    'low': 149.0,
                    'close': 153.0,
                    'volume': 1100000
                }
            ],
            'message': 'Loaded 2 records from database',
            'records': 2,
            'filename': 'AAPL_database.csv'
        }
        
        yield {
            'save': mock_save,
            'load': mock_load
        }


@pytest.fixture(autouse=True)
def setup_logging():
    """Set up logging for tests."""
    with patch('back_end.utils.logger.setup_logging'):
        yield


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Clean up temporary files after tests."""
    yield
    # Cleanup logic can be added here if needed 