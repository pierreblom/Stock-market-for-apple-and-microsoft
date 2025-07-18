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


@stock_bp.route('/stock/<symbol>/signals')
@handle_exceptions
def get_stock_signals(symbol):
    """Get trading signals for a specific symbol"""
    period = request.args.get('period', 'default')
    result = stock_service.get_signals(symbol, period)
    return ApiResponse.success(data=result, message="Trading signals retrieved successfully")


@stock_bp.route('/stock/<symbol>/technical-analysis')
@handle_exceptions
def get_technical_analysis(symbol):
    """Get comprehensive technical analysis for a specific symbol"""
    period = request.args.get('period', 'default')
    result = stock_service.get_technical_analysis(symbol, period)
    return ApiResponse.success(data=result, message="Technical analysis completed successfully")


@stock_bp.route('/stock/<symbol>/indicators')
@handle_exceptions
def get_stock_indicators(symbol):
    """Get technical indicators for a specific symbol"""
    period = request.args.get('period', 'default')
    result = stock_service.get_technical_analysis(symbol, period)
    
    # Extract only the indicators from the full analysis
    if result['success']:
        indicators_data = {
            'symbol': result['symbol'],
            'period': result['period'],
            'indicators': result['indicators'],
            'latest_values': result['latest_values'],
            'analysis_date': result['analysis_date'],
            'data_points': result['data_points']
        }
        return ApiResponse.success(data=indicators_data, message="Technical indicators retrieved successfully")
    else:
        return ApiResponse.error(message=result['message'], status_code=400)


@stock_bp.route('/stock/<symbol>/prediction')
@handle_exceptions
def get_stock_prediction(symbol):
    """Get price predictions for a specific symbol"""
    days_ahead = request.args.get('days', 30, type=int)
    retrain = request.args.get('retrain', 'false').lower() == 'true'
    
    result = stock_service.get_price_prediction(symbol, days_ahead, retrain)
    return ApiResponse.success(data=result, message="Price predictions generated successfully")


@stock_bp.route('/stock/<symbol>/prediction/history')
@handle_exceptions
def get_prediction_history(symbol):
    """Get prediction history for a symbol (placeholder for future implementation)"""
    # This would typically return historical predictions vs actual prices
    return ApiResponse.success(
        data={'symbol': symbol, 'message': 'Prediction history feature coming soon'},
        message="Prediction history endpoint ready"
    )


@stock_bp.route('/stock/<symbol>/model/performance')
@handle_exceptions
def get_model_performance(symbol):
    """Get model performance metrics for a symbol"""
    result = stock_service.get_model_performance(symbol)
    return ApiResponse.success(data=result, message="Model performance retrieved successfully")


@stock_bp.route('/stock/<symbol>/model/retrain', methods=['POST'])
@handle_exceptions
def retrain_model(symbol):
    """Retrain the prediction model for a symbol"""
    days_ahead = request.args.get('days', 30, type=int)
    
    result = stock_service.get_price_prediction(symbol, days_ahead, retrain=True)
    return ApiResponse.success(data=result, message="Model retrained successfully") 