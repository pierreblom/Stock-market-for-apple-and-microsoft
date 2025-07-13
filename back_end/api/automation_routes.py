"""
Automation API routes.
"""

from flask import Blueprint
from ..services.automation_service import AutomationService
from ..utils.response_wrapper import ApiResponse, handle_exceptions

# Create Blueprint
automation_bp = Blueprint('automation', __name__)
automation_service = AutomationService()


@automation_bp.route('/auto-download/trigger')
@handle_exceptions
def trigger_auto_download():
    """Manually trigger the automated download process"""
    result = automation_service.trigger_automated_download()
    return ApiResponse.success(data=result, message="Automated download triggered successfully")


@automation_bp.route('/auto-download/status')
@handle_exceptions
def auto_download_status():
    """Get status of automatic download configuration"""
    result = automation_service.get_automation_status()
    return ApiResponse.success(data=result, message="Automation status retrieved successfully") 