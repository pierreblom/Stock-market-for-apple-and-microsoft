"""
Stock-related API routes.
"""

from flask import Blueprint, request, send_file
from ..services.stock_service import StockService
from ..utils.response_wrapper import ApiResponse, handle_exceptions

# Create Blueprint
stock_bp = Blueprint('stock', __name__)
stock_service = StockService()


@stock_bp.route('/stock_data/<symbol>')
@handle_exceptions
def get_stock_data(symbol):
    """Get stock data from the database or generate it"""
    period = request.args.get('period', 'default')
    result = stock_service.get_stock_data(symbol, period)
    return ApiResponse.success(data=result, message="Stock data retrieved successfully")


@stock_bp.route('/comparison_data')
@handle_exceptions
def get_comparison_data():
    """Get comparison data for multiple symbols"""
    symbols_str = request.args.get('symbols', 'AAPL,MSFT')
    symbols = [s.strip().upper() for s in symbols_str.split(',') if s.strip()]
    
    period = request.args.get('period', 'default')
    month_filter = request.args.get('month', None)
    
    result = stock_service.get_comparison_data(symbols, period, month_filter)
    return ApiResponse.success(data=result, message="Comparison data retrieved successfully")


@stock_bp.route('/database/save/<symbol>')
@handle_exceptions
def save_to_database(symbol):
    """Explicitly save current stock data to CSV database"""
    result = stock_service.save_to_database(symbol)
    return ApiResponse.success(data=result, message="Data saved to database successfully")


@stock_bp.route('/database/load/<symbol>')
@handle_exceptions
def load_from_database(symbol):
    """Load stock data from CSV database"""
    result = stock_service.load_from_database(symbol)
    return ApiResponse.success(data=result, message="Data loaded from database successfully") 