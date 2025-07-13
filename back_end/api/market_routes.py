"""
Market analysis API routes.
"""

from flask import Blueprint, request
from ..services.market_service import MarketService
from ..utils.response_wrapper import ApiResponse, handle_exceptions

# Create Blueprint
market_bp = Blueprint('market', __name__)
market_service = MarketService()


@market_bp.route('/market/correlation')
@handle_exceptions
def get_market_correlation():
    """Advanced market correlation analysis"""
    symbols = request.args.get('symbols', 'NVDA,AAPL,MSFT').split(',')
    period = request.args.get('period', 'default')
    
    result = market_service.get_market_correlation(symbols, period)
    return ApiResponse.success(data=result, message="Correlation analysis completed successfully")


@market_bp.route('/market/events')
@handle_exceptions
def get_market_events():
    """Detect significant market events from price movements"""
    symbol = request.args.get('symbol', 'AAPL').upper()
    threshold = float(request.args.get('threshold', '0.05'))  # 5% default
    
    result = market_service.get_market_events(symbol, threshold)
    return ApiResponse.success(data=result, message="Market events analysis completed successfully") 