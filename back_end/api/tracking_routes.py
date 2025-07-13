"""
Real-time tracking API routes.
"""

import pandas as pd
from datetime import datetime
from flask import Blueprint
from ..config import EXPORT_DIR
from ..utils.response_wrapper import ApiResponse, handle_exceptions

# Create Blueprint
tracking_bp = Blueprint('tracking', __name__)


@tracking_bp.route('/today/real-data')
@handle_exceptions
def show_todays_real_data():
    """Show what real tracking data is available for today from the consolidated file."""
    filename = "price_tracking.csv"
    filepath = EXPORT_DIR / filename
    
    if not filepath.exists():
        return ApiResponse.error(
            message='No tracking file found.',
            data={
                'filename': filename,
                'symbols': [],
                'data_points': {}
            }
        )
    
    # Read the tracking file
    df = pd.read_csv(filepath)
    # Filter out NaN values in symbol column first
    df = df.dropna(subset=['symbol'])
    
    # Filter for today's data
    today_str = datetime.now().strftime('%Y-%m-%d')
    today_df = df[df['date'] == today_str]

    if today_df.empty:
        return ApiResponse.success(
            data={
                'message': f'Tracking file exists, but no data found for today ({today_str}).',
                'filename': filename,
                'symbols': [],
                'data_points': {}
            },
            message="No tracking data for today"
        )

    # Group by symbol
    symbols_available = today_df['symbol'].unique().tolist()
    data_points = {}
    latest_data = {}
    
    for symbol in symbols_available:
        symbol_data = today_df[today_df['symbol'] == symbol]
        data_points[symbol] = len(symbol_data)
        
        # Get latest data point for each symbol
        if len(symbol_data) > 0:
            symbol_data_sorted = symbol_data.copy()
            symbol_data_sorted['timestamp_dt'] = pd.to_datetime(symbol_data_sorted['timestamp'])
            latest = symbol_data_sorted.sort_values('timestamp_dt').iloc[-1]
            latest_data[symbol] = {
                'latest_time': latest['timestamp'],
                'price': float(latest['price']),
                'change': float(latest['change']),
                'change_percent': float(latest['change_percent'])
            }
        else:
            latest_data[symbol] = {
                'latest_time': None,
                'price': 0,
                'change': 0,
                'change_percent': 0
            }

    return ApiResponse.success(
        data={
            'message': f'Found data for {len(symbols_available)} symbols for today.',
            'filename': filename,
            'symbols': symbols_available,
            'data_points': data_points,
            'latest_data': latest_data
        },
        message="Today's tracking data retrieved successfully"
    ) 