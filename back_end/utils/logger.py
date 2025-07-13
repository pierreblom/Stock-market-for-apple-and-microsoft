"""
Logging configuration and utilities for the stock market dashboard.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from ..config import config


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class StructuredFormatter(logging.Formatter):
    """Structured formatter for JSON-like log output."""
    
    def format(self, record):
        # Create structured log entry
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return str(log_entry)


def setup_logging(
    level: str = 'INFO',
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    file_enabled: bool = False,
    file_path: Optional[Path] = None,
    console_enabled: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Setup application logging with console and optional file handlers.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log message format string
        file_enabled: Whether to enable file logging
        file_path: Path to log file
        console_enabled: Whether to enable console logging
        max_file_size: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
    """
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Set root logger level
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Create formatters
    console_formatter = ColoredFormatter(log_format)
    file_formatter = logging.Formatter(log_format)
    structured_formatter = StructuredFormatter()
    
    # Console handler
    if console_enabled:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if file_enabled and file_path:
        # Ensure log directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_function_call(logger: logging.Logger, func_name: str, **kwargs):
    """
    Decorator to log function calls with parameters.
    
    Args:
        logger: Logger instance
        func_name: Name of the function being called
        **kwargs: Function parameters to log
    """
    def decorator(func):
        def wrapper(*args, **func_kwargs):
            # Log function entry
            logger.debug(f"Entering {func_name}", extra={
                'extra_fields': {
                    'function': func_name,
                    'parameters': {**kwargs, **func_kwargs}
                }
            })
            
            try:
                result = func(*args, **func_kwargs)
                logger.debug(f"Exiting {func_name} successfully", extra={
                    'extra_fields': {
                        'function': func_name,
                        'result_type': type(result).__name__
                    }
                })
                return result
            except Exception as e:
                logger.error(f"Error in {func_name}: {str(e)}", extra={
                    'extra_fields': {
                        'function': func_name,
                        'error_type': type(e).__name__
                    }
                }, exc_info=True)
                raise
        
        return wrapper
    return decorator


def log_api_request(logger: logging.Logger, endpoint: str, method: str = 'GET', **kwargs):
    """
    Log API request details.
    
    Args:
        logger: Logger instance
        endpoint: API endpoint being called
        method: HTTP method
        **kwargs: Additional request details
    """
    logger.info(f"API Request: {method} {endpoint}", extra={
        'extra_fields': {
            'api_request': {
                'method': method,
                'endpoint': endpoint,
                **kwargs
            }
        }
    })


def log_api_response(logger: logging.Logger, endpoint: str, status_code: int, response_time: float, **kwargs):
    """
    Log API response details.
    
    Args:
        logger: Logger instance
        endpoint: API endpoint that was called
        status_code: HTTP status code
        response_time: Response time in seconds
        **kwargs: Additional response details
    """
    level = logging.ERROR if status_code >= 400 else logging.INFO
    logger.log(level, f"API Response: {status_code} {endpoint} ({response_time:.3f}s)", extra={
        'extra_fields': {
            'api_response': {
                'endpoint': endpoint,
                'status_code': status_code,
                'response_time': response_time,
                **kwargs
            }
        }
    })


def log_data_operation(logger: logging.Logger, operation: str, symbol: str, records_count: int = 0, **kwargs):
    """
    Log data operations (fetch, save, load, etc.).
    
    Args:
        logger: Logger instance
        operation: Type of operation (fetch, save, load, etc.)
        symbol: Stock symbol
        records_count: Number of records processed
        **kwargs: Additional operation details
    """
    logger.info(f"Data {operation}: {symbol} ({records_count} records)", extra={
        'extra_fields': {
            'data_operation': {
                'operation': operation,
                'symbol': symbol,
                'records_count': records_count,
                **kwargs
            }
        }
    })


def log_error(logger: logging.Logger, error: Exception, context: str = "", **kwargs):
    """
    Log errors with context information.
    
    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Context where the error occurred
        **kwargs: Additional context information
    """
    logger.error(f"Error in {context}: {str(error)}", extra={
        'extra_fields': {
            'error_context': context,
            'error_type': type(error).__name__,
            **kwargs
        }
    }, exc_info=True)


# Initialize logging when module is imported
setup_logging(
    level=config.logging.level,
    log_format=config.logging.format,
    file_enabled=config.logging.file_enabled,
    file_path=config.logging.file_path,
    console_enabled=config.logging.console_enabled
) 