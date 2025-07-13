"""
Tests for API routes.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from back_end.app import create_app
from back_end.utils.exceptions import DataFetchException, DatabaseException


class TestHealthRoutes:
    """Test health check routes."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.client = self.app.test_client()
    
    def test_health_check_success(self):
        """Test successful health check."""
        response = self.client.get('/api/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'status' in data['data']
        assert 'config' in data['data']
        assert data['data']['status'] == 'healthy'


class TestStockRoutes:
    """Test stock data routes."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.client = self.app.test_client()
    
    @patch('back_end.api.stock_routes.stock_service')
    def test_get_stock_data_success(self, mock_service):
        """Test successful stock data retrieval."""
        # Mock the service response
        mock_service.get_stock_data.return_value = {
            'success': True,
            'symbol': 'AAPL',
            'dates': ['2023-01-01', '2023-01-02'],
            'prices': [150.0, 155.0],
            'volumes': [1000, 1100],
            'current': {'price': 155.0, 'change': 5.0},
            'errors': [],
            'messages': {'historical': 'Data loaded', 'current': 'From database'},
            'granularity': 'daily'
        }
        
        response = self.client.get('/api/stock_data/AAPL?period=default')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['symbol'] == 'AAPL'
        assert len(data['data']['dates']) == 2
        assert len(data['data']['prices']) == 2
    
    @patch('back_end.api.stock_routes.stock_service')
    def test_get_stock_data_service_error(self, mock_service):
        """Test stock data retrieval with service error."""
        # Mock the service to raise an exception
        mock_service.get_stock_data.side_effect = DataFetchException("API error")
        
        response = self.client.get('/api/stock_data/AAPL')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert 'API error' in data['message']
    
    @patch('back_end.api.stock_routes.stock_service')
    def test_comparison_data_success(self, mock_service):
        """Test successful comparison data retrieval."""
        # Mock the service response
        mock_service.get_comparison_data.return_value = {
            'success': True,
            'data': {
                'AAPL': {
                    'success': True,
                    'dates': ['2023-01-01'],
                    'prices': [150.0],
                    'current': {'price': 150.0}
                },
                'MSFT': {
                    'success': True,
                    'dates': ['2023-01-01'],
                    'prices': [300.0],
                    'current': {'price': 300.0}
                }
            },
            'errors': []
        }
        
        response = self.client.get('/api/comparison_data?symbols=AAPL,MSFT')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'AAPL' in data['data']['data']
        assert 'MSFT' in data['data']['data']
    
    @patch('back_end.api.stock_routes.stock_service')
    def test_save_to_database_success(self, mock_service):
        """Test successful database save."""
        # Mock the service response
        mock_service.save_to_database.return_value = {
            'success': True,
            'symbol': 'AAPL',
            'message': 'Database updated successfully',
            'records_added': 10,
            'total_records': 100,
            'updated': True,
            'filename': 'AAPL_database.csv'
        }
        
        response = self.client.get('/api/database/save/AAPL')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['symbol'] == 'AAPL'
        assert data['data']['records_added'] == 10


class TestMarketRoutes:
    """Test market analysis routes."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.client = self.app.test_client()
    
    @patch('back_end.api.market_routes.market_service')
    def test_market_correlation_success(self, mock_service):
        """Test successful market correlation analysis."""
        # Mock the service response
        mock_service.get_market_correlation.return_value = {
            'success': True,
            'correlation_matrix': {
                'AAPL': {'AAPL': 1.0, 'MSFT': 0.8},
                'MSFT': {'AAPL': 0.8, 'MSFT': 1.0}
            },
            'market_volatility': {'AAPL': 0.2, 'MSFT': 0.18},
            'symbols': ['AAPL', 'MSFT'],
            'analysis_date': '2023-01-01 12:00:00',
            'message': 'Correlation analysis complete'
        }
        
        response = self.client.get('/api/market/correlation?symbols=AAPL,MSFT')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert 'correlation_matrix' in data['data']
        assert 'market_volatility' in data['data']
    
    @patch('back_end.api.market_routes.market_service')
    def test_market_events_success(self, mock_service):
        """Test successful market events detection."""
        # Mock the service response
        mock_service.get_market_events.return_value = {
            'success': True,
            'symbol': 'AAPL',
            'threshold': 5.0,
            'events': [
                {
                    'date': '2023-01-02',
                    'type': 'Large Move Up',
                    'magnitude': 'Significant',
                    'return': 10.0,
                    'price_from': 100.0,
                    'price_to': 110.0,
                    'volume': 1000
                }
            ],
            'total_events': 1,
            'analysis_date': '2023-01-01 12:00:00'
        }
        
        response = self.client.get('/api/market/events?symbol=AAPL&threshold=0.05')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['symbol'] == 'AAPL'
        assert len(data['data']['events']) == 1


class TestDatabaseRoutes:
    """Test database management routes."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.client = self.app.test_client()
    
    @patch('back_end.api.database_routes.database_service')
    def test_list_csv_files_success(self, mock_service):
        """Test successful CSV file listing."""
        # Mock the service response
        mock_service.list_csv_files.return_value = {
            'success': True,
            'files': [
                {
                    'filename': 'test1.csv',
                    'size': 1024,
                    'created': '2023-01-01T00:00:00',
                    'modified': '2023-01-01T00:00:00'
                }
            ],
            'count': 1
        }
        
        response = self.client.get('/api/csv/list')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['count'] == 1
        assert len(data['data']['files']) == 1
    
    @patch('back_end.api.database_routes.database_service')
    def test_list_database_files_success(self, mock_service):
        """Test successful database file listing."""
        # Mock the service response
        mock_service.list_database_files.return_value = {
            'success': True,
            'databases': [
                {
                    'symbol': 'AAPL',
                    'filename': 'AAPL_database.csv',
                    'records': 100,
                    'size_kb': 10.5,
                    'last_modified': 1234567890,
                    'date_range': {
                        'earliest': '2023-01-01',
                        'latest': '2023-12-31'
                    }
                }
            ],
            'total_files': 1,
            'message': 'Found 1 database files'
        }
        
        response = self.client.get('/api/database/list')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['total_files'] == 1
        assert len(data['data']['databases']) == 1
    
    @patch('back_end.api.database_routes.database_service')
    def test_update_all_databases_success(self, mock_service):
        """Test successful database update."""
        # Mock the service response
        mock_service.update_all_databases.return_value = {
            'success': True,
            'results': {
                'AAPL': {
                    'success': True,
                    'message': 'Updated successfully',
                    'records_added': 10,
                    'total_records': 100,
                    'updated': True
                }
            },
            'summary': {
                'successful_symbols': 1,
                'total_symbols': 1,
                'total_records': 100
            },
            'message': 'Updated 1/1 databases'
        }
        
        response = self.client.get('/api/database/update-all')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['summary']['successful_symbols'] == 1


class TestAutomationRoutes:
    """Test automation routes."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.client = self.app.test_client()
    
    @patch('back_end.api.automation_routes.automation_service')
    def test_automation_status_success(self, mock_service):
        """Test successful automation status retrieval."""
        # Mock the service response
        mock_service.get_automation_status.return_value = {
            'success': True,
            'config': {
                'enabled': True,
                'hour': 18,
                'minute': 0,
                'symbols': ['AAPL'],
                'api_key_configured': True
            },
            'next_run': '18:00 daily'
        }
        
        response = self.client.get('/api/auto-download/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['config']['enabled'] is True
        assert data['data']['config']['hour'] == 18
    
    @patch('back_end.api.automation_routes.automation_service')
    def test_trigger_automated_download_success(self, mock_service):
        """Test successful automated download triggering."""
        # Mock the service response
        mock_service.trigger_automated_download.return_value = {
            'success': True,
            'message': 'Download triggered successfully',
            'results': {
                'AAPL': {'success': True, 'records': 10}
            },
            'summary': {
                'successful_symbols': 1,
                'total_symbols': 1,
                'total_records': 10
            }
        }
        
        response = self.client.get('/api/auto-download/trigger')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['summary']['successful_symbols'] == 1 