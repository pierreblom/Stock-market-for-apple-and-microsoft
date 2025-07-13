"""
Custom exceptions for the stock market dashboard backend.
"""


class StockDashboardException(Exception):
    """Base exception for all stock dashboard errors."""
    pass


class ApiKeyNotConfiguredException(StockDashboardException):
    """Raised when required API keys are not configured."""
    pass


class DataFetchException(StockDashboardException):
    """Raised when data fetching fails."""
    pass


class DatabaseException(StockDashboardException):
    """Raised when database operations fail."""
    pass


class ValidationException(StockDashboardException):
    """Raised when input validation fails."""
    pass


class FileNotFoundException(StockDashboardException):
    """Raised when a required file is not found."""
    pass 