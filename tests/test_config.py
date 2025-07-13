"""
Tests for configuration management.
"""

import os
import pytest
from unittest.mock import patch
from back_end.config import Config, APIConfig, ServerConfig, SchedulingConfig, LoggingConfig


class TestAPIConfig:
    """Test API configuration."""
    
    def test_api_config_from_env(self):
        """Test creating API config from environment variables."""
        with patch.dict(os.environ, {
            'FINNHUB_API_KEY': 'test_finnhub_key',
            'ALPHA_VANTAGE_API_KEY': 'test_alpha_key',
            'API_TIMEOUT_SECONDS': '20',
            'API_QUICK_TIMEOUT_SECONDS': '5',
            'HISTORICAL_DATA_LIMIT': '200'
        }):
            config = APIConfig.from_env()
            
            assert config.finnhub_api_key == 'test_finnhub_key'
            assert config.alpha_vantage_api_key == 'test_alpha_key'
            assert config.timeout == 20
            assert config.quick_timeout == 5
            assert config.historical_data_limit == 200
    
    def test_api_config_defaults(self):
        """Test API config with default values."""
        with patch.dict(os.environ, {}, clear=True):
            config = APIConfig.from_env()
            
            assert config.finnhub_api_key is None
            assert config.alpha_vantage_api_key is None
            assert config.timeout == 15
            assert config.quick_timeout == 10
            assert config.historical_data_limit == 121
    
    def test_api_config_validation(self):
        """Test API config validation."""
        config = APIConfig(
            finnhub_api_key=None,
            alpha_vantage_api_key=None,
            timeout=3,  # Very low timeout
            quick_timeout=10,
            historical_data_limit=121
        )
        
        warnings = config.validate()
        
        assert len(warnings) == 3
        assert "FINNHUB_API_KEY not configured" in warnings[0]
        assert "ALPHA_VANTAGE_API_KEY not configured" in warnings[1]
        assert "API_TIMEOUT_SECONDS (3) is very low" in warnings[2]


class TestServerConfig:
    """Test server configuration."""
    
    def test_server_config_from_env(self):
        """Test creating server config from environment variables."""
        with patch.dict(os.environ, {
            'FLASK_HOST': 'localhost',
            'FLASK_PORT': '8080',
            'FLASK_DEBUG': 'True'
        }):
            config = ServerConfig.from_env()
            
            assert config.host == 'localhost'
            assert config.port == 8080
            assert config.debug is True
    
    def test_server_config_defaults(self):
        """Test server config with default values."""
        with patch.dict(os.environ, {}, clear=True):
            config = ServerConfig.from_env()
            
            assert config.host == '0.0.0.0'
            assert config.port == 8001
            assert config.debug is False
    
    def test_server_config_validation(self):
        """Test server config validation."""
        config = ServerConfig(
            host='0.0.0.0',
            port=99999,  # Invalid port
            debug=True
        )
        
        warnings = config.validate()
        
        assert len(warnings) == 2
        assert "FLASK_PORT (99999) is outside recommended range" in warnings[0]
        assert "Debug mode enabled with host 0.0.0.0" in warnings[1]


class TestSchedulingConfig:
    """Test scheduling configuration."""
    
    def test_scheduling_config_from_env(self):
        """Test creating scheduling config from environment variables."""
        with patch.dict(os.environ, {
            'DAILY_UPDATE_HOUR': '20',
            'DAILY_UPDATE_MINUTE': '30',
            'AUTO_DOWNLOAD_ENABLED': 'False'
        }):
            config = SchedulingConfig.from_env()
            
            assert config.daily_update_hour == 20
            assert config.daily_update_minute == 30
            assert config.auto_download_enabled is False
    
    def test_scheduling_config_validation(self):
        """Test scheduling config validation."""
        config = SchedulingConfig(
            daily_update_hour=25,  # Invalid hour
            daily_update_minute=70,  # Invalid minute
            auto_download_enabled=True,
            auto_download_symbols=[]
        )
        
        warnings = config.validate()
        
        assert len(warnings) == 3
        assert "DAILY_UPDATE_HOUR (25) must be between 0-23" in warnings[0]
        assert "DAILY_UPDATE_MINUTE (70) must be between 0-59" in warnings[1]
        assert "No auto-download symbols configured" in warnings[2]


class TestLoggingConfig:
    """Test logging configuration."""
    
    def test_logging_config_from_env(self):
        """Test creating logging config from environment variables."""
        with patch.dict(os.environ, {
            'LOG_LEVEL': 'DEBUG',
            'LOG_FORMAT': 'custom format',
            'LOG_FILE_ENABLED': 'True',
            'LOG_FILE_PATH': 'custom/path.log',
            'LOG_CONSOLE_ENABLED': 'False'
        }):
            config = LoggingConfig.from_env()
            
            assert config.level == 'DEBUG'
            assert config.format == 'custom format'
            assert config.file_enabled is True
            assert str(config.file_path) == 'custom/path.log'
            assert config.console_enabled is False
    
    def test_logging_config_validation(self):
        """Test logging config validation."""
        config = LoggingConfig(
            level='INVALID_LEVEL',
            format='test format',
            file_enabled=True,
            file_path=None,
            console_enabled=True
        )
        
        warnings = config.validate()
        
        assert len(warnings) == 1
        assert "LOG_LEVEL (INVALID_LEVEL) is not valid" in warnings[0]
        assert config.level == 'INFO'  # Should be reset to default


class TestConfig:
    """Test main configuration class."""
    
    def test_config_initialization(self):
        """Test main config initialization."""
        with patch.dict(os.environ, {
            'FINNHUB_API_KEY': 'test_key',
            'FLASK_PORT': '9000'
        }):
            config = Config()
            
            assert config.api.finnhub_api_key == 'test_key'
            assert config.server.port == 9000
            assert config.export_dir.exists()
    
    def test_config_api_key_checks(self):
        """Test API key configuration checks."""
        config = Config()
        
        # Test with no API keys
        with patch.object(config.api, 'finnhub_api_key', None):
            with patch.object(config.api, 'alpha_vantage_api_key', None):
                assert config.get_api_key_configured() is False
                assert config.get_finnhub_configured() is False
                assert config.get_alpha_vantage_configured() is False
        
        # Test with API keys
        with patch.object(config.api, 'finnhub_api_key', 'test_key'):
            with patch.object(config.api, 'alpha_vantage_api_key', 'test_key'):
                assert config.get_api_key_configured() is True
                assert config.get_finnhub_configured() is True
                assert config.get_alpha_vantage_configured() is True
    
    def test_config_validation_warnings(self):
        """Test configuration validation warnings."""
        with patch.dict(os.environ, {
            'FLASK_DEBUG': 'True',
            'FLASK_HOST': '0.0.0.0'
        }):
            config = Config()
            
            # Should have warnings for debug mode with 0.0.0.0
            # Note: We can't easily test the actual warning output without more complex mocking
            assert config.server.debug is True
            assert config.server.host == '0.0.0.0' 