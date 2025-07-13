"""
Configuration management for the stock market dashboard.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class APIConfig:
    """API configuration settings."""
    finnhub_api_key: Optional[str]
    alpha_vantage_api_key: Optional[str]
    timeout: int
    quick_timeout: int
    historical_data_limit: int
    
    @classmethod
    def from_env(cls) -> 'APIConfig':
        """Create API config from environment variables."""
        return cls(
            finnhub_api_key=os.getenv('FINNHUB_API_KEY'),
            alpha_vantage_api_key=os.getenv('ALPHA_VANTAGE_API_KEY'),
            timeout=int(os.getenv('API_TIMEOUT_SECONDS', 15)),
            quick_timeout=int(os.getenv('API_QUICK_TIMEOUT_SECONDS', 10)),
            historical_data_limit=int(os.getenv('HISTORICAL_DATA_LIMIT', 121))
        )
    
    def validate(self) -> List[str]:
        """Validate API configuration and return list of warnings."""
        warnings = []
        
        if not self.finnhub_api_key:
            warnings.append("FINNHUB_API_KEY not configured - current data fetching will be disabled")
        
        if not self.alpha_vantage_api_key:
            warnings.append("ALPHA_VANTAGE_API_KEY not configured - historical data fetching will be disabled")
        
        if self.timeout < 5:
            warnings.append(f"API_TIMEOUT_SECONDS ({self.timeout}) is very low, consider increasing")
        
        return warnings


@dataclass
class ServerConfig:
    """Server configuration settings."""
    host: str
    port: int
    debug: bool
    
    @classmethod
    def from_env(cls) -> 'ServerConfig':
        """Create server config from environment variables."""
        return cls(
            host=os.getenv('FLASK_HOST', '0.0.0.0'),
            port=int(os.getenv('FLASK_PORT', 8001)),
            debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        )
    
    def validate(self) -> List[str]:
        """Validate server configuration and return list of warnings."""
        warnings = []
        
        if self.port < 1024 or self.port > 65535:
            warnings.append(f"FLASK_PORT ({self.port}) is outside recommended range (1024-65535)")
        
        if self.debug and self.host == '0.0.0.0':
            warnings.append("Debug mode enabled with host 0.0.0.0 - consider using localhost for development")
        
        return warnings


@dataclass
class SchedulingConfig:
    """Scheduling configuration settings."""
    daily_update_hour: int
    daily_update_minute: int
    auto_download_enabled: bool
    auto_download_symbols: List[str]
    
    @classmethod
    def from_env(cls) -> 'SchedulingConfig':
        """Create scheduling config from environment variables."""
        return cls(
            daily_update_hour=int(os.getenv('DAILY_UPDATE_HOUR', 19)),
            daily_update_minute=int(os.getenv('DAILY_UPDATE_MINUTE', 0)),
            auto_download_enabled=os.getenv('AUTO_DOWNLOAD_ENABLED', 'True').lower() == 'true',
            auto_download_symbols=['NVDA']  # Default symbols
        )
    
    def validate(self) -> List[str]:
        """Validate scheduling configuration and return list of warnings."""
        warnings = []
        
        if not (0 <= self.daily_update_hour <= 23):
            warnings.append(f"DAILY_UPDATE_HOUR ({self.daily_update_hour}) must be between 0-23")
        
        if not (0 <= self.daily_update_minute <= 59):
            warnings.append(f"DAILY_UPDATE_MINUTE ({self.daily_update_minute}) must be between 0-59")
        
        if not self.auto_download_symbols:
            warnings.append("No auto-download symbols configured")
        
        return warnings


@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    level: str
    format: str
    file_enabled: bool
    file_path: Optional[Path]
    console_enabled: bool
    
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """Create logging config from environment variables."""
        return cls(
            level=os.getenv('LOG_LEVEL', 'INFO'),
            format=os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            file_enabled=os.getenv('LOG_FILE_ENABLED', 'False').lower() == 'true',
            file_path=Path(os.getenv('LOG_FILE_PATH', 'logs/stock_dashboard.log')) if os.getenv('LOG_FILE_ENABLED', 'False').lower() == 'true' else None,
            console_enabled=os.getenv('LOG_CONSOLE_ENABLED', 'True').lower() == 'true'
        )
    
    def validate(self) -> List[str]:
        """Validate logging configuration and return list of warnings."""
        warnings = []
        
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.level.upper() not in valid_levels:
            warnings.append(f"LOG_LEVEL ({self.level}) is not valid, using INFO")
            self.level = 'INFO'
        
        if self.file_enabled and self.file_path:
            # Ensure log directory exists
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        return warnings


class Config:
    """Main configuration class that manages all application settings."""
    
    def __init__(self):
        # Load environment variables
        load_dotenv(override=True)
        
        # Initialize configuration sections
        self.api = APIConfig.from_env()
        self.server = ServerConfig.from_env()
        self.scheduling = SchedulingConfig.from_env()
        self.logging = LoggingConfig.from_env()
        
        # Directories
        self.export_dir = Path("data_exports")
        self.export_dir.mkdir(exist_ok=True)
        
        # Validate all configurations
        self._validate_all()
    
    def _validate_all(self):
        """Validate all configuration sections and log warnings."""
        all_warnings = []
        
        all_warnings.extend(self.api.validate())
        all_warnings.extend(self.server.validate())
        all_warnings.extend(self.scheduling.validate())
        all_warnings.extend(self.logging.validate())
        
        if all_warnings:
            logging.warning("Configuration warnings:")
            for warning in all_warnings:
                logging.warning(f"  - {warning}")
    
    def get_api_key_configured(self) -> bool:
        """Check if any API key is configured."""
        return bool(self.api.finnhub_api_key or self.api.alpha_vantage_api_key)
    
    def get_finnhub_configured(self) -> bool:
        """Check if Finnhub API is configured."""
        return bool(self.api.finnhub_api_key)
    
    def get_alpha_vantage_configured(self) -> bool:
        """Check if Alpha Vantage API is configured."""
        return bool(self.api.alpha_vantage_api_key)


# Create global config instance
config = Config()

# Backward compatibility exports
FINNHUB_API_KEY = config.api.finnhub_api_key
ALPHA_VANTAGE_API_KEY = config.api.alpha_vantage_api_key
API_TIMEOUT = config.api.timeout
API_QUICK_TIMEOUT = config.api.quick_timeout
HISTORICAL_DATA_LIMIT = config.api.historical_data_limit

FLASK_HOST = config.server.host
FLASK_PORT = config.server.port
FLASK_DEBUG = config.server.debug

DAILY_UPDATE_HOUR = config.scheduling.daily_update_hour
DAILY_UPDATE_MINUTE = config.scheduling.daily_update_minute
AUTO_DOWNLOAD_ENABLED = config.scheduling.auto_download_enabled
AUTO_DOWNLOAD_SYMBOLS = config.scheduling.auto_download_symbols

EXPORT_DIR = config.export_dir