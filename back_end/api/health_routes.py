"""
Health check and system status API routes.
"""

from flask import Blueprint
from ..config import config
from ..utils.response_wrapper import ApiResponse, handle_exceptions
from ..utils.logger import get_logger

# Create Blueprint
health_bp = Blueprint('health', __name__)
logger = get_logger(__name__)


@health_bp.route('/health')
@handle_exceptions
def health_check():
    """Health check endpoint"""
    logger.info("Health check requested")
    
    # Check if API key is configured
    api_key_configured = config.get_api_key_configured()
    finnhub_configured = config.get_finnhub_configured()
    alpha_vantage_configured = config.get_alpha_vantage_configured()
    
    return ApiResponse.success(
        data={
            'status': 'healthy',
            'message': 'Stock dashboard is running',
            'config': {
                'api_key_configured': api_key_configured,
                'finnhub_configured': finnhub_configured,
                'alpha_vantage_configured': alpha_vantage_configured,
                'api_timeout': f"{config.api.timeout}s",
                'server': {
                    'host': config.server.host,
                    'port': config.server.port,
                    'debug': config.server.debug
                },
                'scheduling': {
                    'auto_download_enabled': config.scheduling.auto_download_enabled,
                    'daily_update_hour': config.scheduling.daily_update_hour,
                    'daily_update_minute': config.scheduling.daily_update_minute
                }
            }
        },
        message="Health check completed successfully"
    ) 