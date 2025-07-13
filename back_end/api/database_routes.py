"""
Database management API routes.
"""

from flask import Blueprint, request, send_file
from ..services.database_service import DatabaseService
from ..utils.response_wrapper import ApiResponse, handle_exceptions

# Create Blueprint
database_bp = Blueprint('database', __name__)
database_service = DatabaseService()


@database_bp.route('/csv/list')
@handle_exceptions
def list_csv_files():
    """List all available CSV files"""
    result = database_service.list_csv_files()
    return ApiResponse.success(data=result, message="CSV files listed successfully")


@database_bp.route('/csv/download/<filename>')
@handle_exceptions
def download_csv(filename):
    """Download a specific CSV file"""
    filepath = database_service.get_file_path(filename)
    
    return send_file(
        filepath,
        as_attachment=True,
        download_name=filename,
        mimetype='text/csv'
    )


@database_bp.route('/csv/export/<symbol>')
@handle_exceptions
def export_stock_data_csv(symbol):
    """Export current stock data to CSV and download immediately"""
    period = request.args.get('period', 'all')
    month_filter = request.args.get('month', None)
    
    result = database_service.export_stock_data_csv(symbol, period, month_filter)
    
    return send_file(
        result['filepath'],
        as_attachment=True,
        download_name=result['filename'],
        mimetype='text/csv'
    )


@database_bp.route('/database/list')
@handle_exceptions
def list_database_files():
    """List all available CSV database files"""
    result = database_service.list_database_files()
    return ApiResponse.success(data=result, message="Database files listed successfully")


@database_bp.route('/database/update-all')
@handle_exceptions
def update_all_databases():
    """Update all database files with fresh data"""
    result = database_service.update_all_databases()
    return ApiResponse.success(data=result, message="All databases updated successfully")


@database_bp.route('/database/update-from-tracking', methods=['POST'])
@handle_exceptions
def update_from_tracking():
    """Update database files from the real-time tracking file."""
    result = database_service.update_from_tracking()
    return ApiResponse.success(data=result, message="Database updated from tracking successfully")


@database_bp.route('/cleanup')
@handle_exceptions
def trigger_cleanup():
    """Manual cleanup trigger for duplicate files"""
    result = database_service.cleanup_duplicates()
    return ApiResponse.success(data=result, message="Cleanup completed successfully") 