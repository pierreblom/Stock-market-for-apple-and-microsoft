"""
Tests for service layer components.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from back_end.services.stock_service import StockService
from back_end.services.market_service import MarketService
from back_end.services.database_service import DatabaseService
from back_end.services.automation_service import AutomationService
from back_end.utils.exceptions import DataFetchException, DatabaseException


class TestStockService:
    """Test stock service functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.stock_service = StockService()
    
    @patch('back_end.services.stock_service.MarketDataFetcher')
    def test_get_stock_data_success(self, mock_fetcher):
        """Test successful stock data retrieval."""
        # Mock the fetcher
        mock_fetcher_instance = Mock()
        mock_fetcher_instance.get_current_data.return_value = {
            'success': True,
            'data': {'price': 150.0, 'symbol': 'AAPL'}
        }
        self.stock_service.fetcher = mock_fetcher_instance
        
        # Mock database load with complete OHLCV data
        with patch('back_end.services.stock_service.load_from_database_csv') as mock_load:
            mock_load.return_value = {
                'success': True,
                'data': [
                    {'date': '2023-01-01', 'open': 148.0, 'high': 152.0, 'low': 147.0, 'close': 150.0, 'volume': 1000},
                    {'date': '2023-01-02', 'open': 150.0, 'high': 157.0, 'low': 149.0, 'close': 155.0, 'volume': 1100}
                ]
            }
            
            result = self.stock_service.get_stock_data('AAPL', 'default')
            
            assert result['success'] is True
            assert result['symbol'] == 'AAPL'
            assert len(result['dates']) == 2
            assert len(result['prices']) == 2
    
    @patch('back_end.services.stock_service.MarketDataFetcher')
    def test_get_stock_data_fetch_error(self, mock_fetcher):
        """Test stock data retrieval with fetch error."""
        # Mock the fetcher to raise an exception
        mock_fetcher_instance = Mock()
        mock_fetcher_instance.get_current_data.side_effect = DataFetchException("API error")
        self.stock_service.fetcher = mock_fetcher_instance
        
        with pytest.raises(DataFetchException):
            self.stock_service.get_stock_data('AAPL', 'default')
    
    @patch('back_end.services.stock_service.MarketDataFetcher')
    def test_save_to_database_success(self, mock_fetcher):
        """Test successful database save operation."""
        # Mock the fetcher
        mock_fetcher_instance = Mock()
        mock_fetcher_instance.get_historical_data.return_value = {
            'success': True,
            'data': [
                {'date': '2023-01-01', 'close': 150.0, 'volume': 1000},
                {'date': '2023-01-02', 'close': 155.0, 'volume': 1100}
            ]
        }
        self.stock_service.fetcher = mock_fetcher_instance
        
        # Mock database save
        with patch('back_end.services.stock_service.save_to_database_csv') as mock_save:
            mock_save.return_value = {
                'success': True,
                'records': 2,
                'total_records': 2,
                'message': 'Database updated successfully',
                'updated': True,
                'filename': 'AAPL_database.csv'
            }
            
            result = self.stock_service.save_to_database('AAPL')
            
            assert result['success'] is True
            assert result['symbol'] == 'AAPL'
            assert result['records_added'] == 2
    
    @patch('back_end.services.stock_service.MarketDataFetcher')
    def test_save_to_database_fetch_error(self, mock_fetcher):
        """Test database save with fetch error."""
        # Mock the fetcher to raise an exception
        mock_fetcher_instance = Mock()
        mock_fetcher_instance.get_historical_data.side_effect = DataFetchException("No data available")
        self.stock_service.fetcher = mock_fetcher_instance
        
        with pytest.raises(DataFetchException):
            self.stock_service.save_to_database('AAPL')


class TestMarketService:
    """Test market service functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.market_service = MarketService()
    
    @patch('back_end.services.market_service.MarketDataFetcher')
    def test_get_market_correlation_success(self, mock_fetcher):
        """Test successful market correlation analysis."""
        # Mock the fetcher
        mock_fetcher_instance = Mock()
        mock_fetcher_instance.get_historical_data.return_value = {
            'success': True,
            'data': [
                {'date': '2023-01-01', 'close': 100.0},
                {'date': '2023-01-02', 'close': 105.0},
                {'date': '2023-01-03', 'close': 110.0}
            ]
        }
        self.market_service.fetcher = mock_fetcher_instance
        
        result = self.market_service.get_market_correlation(['AAPL', 'MSFT'])
        
        assert result['success'] is True
        assert 'correlation_matrix' in result
        assert 'market_volatility' in result
        assert 'symbols' in result
    
    @patch('back_end.services.market_service.MarketDataFetcher')
    def test_get_market_events_success(self, mock_fetcher):
        """Test successful market events detection."""
        # Mock the fetcher
        mock_fetcher_instance = Mock()
        mock_fetcher_instance.get_historical_data.return_value = {
            'success': True,
            'data': [
                {'date': '2023-01-01', 'close': 100.0, 'volume': 1000},
                {'date': '2023-01-02', 'close': 110.0, 'volume': 1100},  # 10% increase
                {'date': '2023-01-03', 'close': 95.0, 'volume': 900}    # 13.6% decrease
            ]
        }
        self.market_service.fetcher = mock_fetcher_instance
        
        result = self.market_service.get_market_events('AAPL', threshold=0.05)
        
        assert result['success'] is True
        assert result['symbol'] == 'AAPL'
        assert len(result['events']) >= 1  # Should detect the large moves
    
    @patch('back_end.services.market_service.MarketDataFetcher')
    def test_get_market_events_no_data(self, mock_fetcher):
        """Test market events with no data."""
        # Mock the fetcher to return no data
        mock_fetcher_instance = Mock()
        mock_fetcher_instance.get_historical_data.return_value = {
            'success': False,
            'data': []
        }
        self.market_service.fetcher = mock_fetcher_instance
        
        with pytest.raises(DataFetchException):
            self.market_service.get_market_events('AAPL')


class TestDatabaseService:
    """Test database service functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.db_service = DatabaseService()
    
    @patch('back_end.services.database_service.EXPORT_DIR')
    def test_list_csv_files_success(self, mock_export_dir):
        """Test successful CSV file listing."""
        # Mock the export directory
        mock_dir = Mock()
        mock_file1 = Mock()
        mock_file1.name = 'test1.csv'
        mock_file1.stat.return_value = Mock(st_size=1024, st_ctime=1234567890, st_mtime=1234567890)
        
        mock_file2 = Mock()
        mock_file2.name = 'test2.csv'
        mock_file2.stat.return_value = Mock(st_size=2048, st_ctime=1234567891, st_mtime=1234567891)
        
        mock_dir.glob.return_value = [mock_file1, mock_file2]
        mock_dir.exists.return_value = True
        mock_export_dir.exists.return_value = True
        mock_export_dir.glob.return_value = [mock_file1, mock_file2]
        
        result = self.db_service.list_csv_files()
        
        assert result['success'] is True
        assert result['count'] == 2
        assert len(result['files']) == 2
    
    @patch('back_end.services.database_service.EXPORT_DIR')
    def test_list_database_files_success(self, mock_export_dir):
        """Test successful database file listing."""
        # Mock the export directory
        mock_file = Mock()
        mock_file.name = 'AAPL_database.csv'
        mock_file.stem = 'AAPL_database'
        mock_file.stat.return_value = Mock(st_size=1024, st_mtime=1234567890)
        
        mock_export_dir.glob.return_value = [mock_file]
        
        # Mock pandas read_csv
        with patch('back_end.services.database_service.pd.read_csv') as mock_read_csv:
            mock_df = Mock()
            mock_df.__len__ = lambda x: 100
            mock_df.columns = ['date', 'close', 'volume']
            
            # Mock the date column properly
            mock_date_series = Mock()
            mock_date_series.min.return_value = '2023-01-01'
            mock_date_series.max.return_value = '2023-12-31'
            mock_df.__getitem__ = lambda x, key: mock_date_series if key == 'date' else Mock()
            
            mock_read_csv.return_value = mock_df
            
            result = self.db_service.list_database_files()
            
            assert result['success'] is True
            assert result['total_files'] == 1
            assert len(result['databases']) == 1
    
    def test_get_file_path_security_check(self):
        """Test file path security validation."""
        # Test path traversal attempt
        with pytest.raises(Exception):  # Should raise FileNotFoundException
            self.db_service.get_file_path('../../../etc/passwd')
        
        # Test invalid filename with slashes
        with pytest.raises(Exception):
            self.db_service.get_file_path('file/with/slashes.csv')


class TestAutomationService:
    """Test automation service functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.automation_service = AutomationService()
    
    @patch.multiple('back_end.services.automation_service',
                   FINNHUB_API_KEY='d1n3591r01qlvnp5a50gd1n3591r01qlvnp5a510',
                   AUTO_DOWNLOAD_SYMBOLS=['NVDA'],
                   DAILY_UPDATE_MINUTE=0,
                   DAILY_UPDATE_HOUR=19,
                   AUTO_DOWNLOAD_ENABLED=True)
    def test_get_automation_status(self):
        """Test automation status retrieval."""
        result = self.automation_service.get_automation_status()
        
        assert result['success'] is True
        assert result['config']['enabled'] is True
        assert result['config']['hour'] == 19
        assert result['config']['minute'] == 0
        assert result['config']['symbols'] == ['NVDA']
        assert result['config']['api_key_configured'] is True
    
    @patch('back_end.services.automation_service.automated_daily_download')
    def test_trigger_automated_download(self, mock_download):
        """Test automated download triggering."""
        # Mock the download function
        mock_download.return_value = {
            'AAPL': {'success': True, 'records': 10},
            'MSFT': {'success': False, 'records': 0}
        }
        
        result = self.automation_service.trigger_automated_download()
        
        assert result['success'] is True
        assert result['summary']['successful_symbols'] == 1
        assert result['summary']['total_symbols'] == 2
        assert result['summary']['total_records'] == 10 