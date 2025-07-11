import pandas as pd
import logging
from datetime import datetime, timedelta
from ..config import EXPORT_DIR


def save_price_tracking_data(symbol, current_data):
    """Save current price data to a single historical tracking file."""
    try:
        if not current_data:
            return None
            
        # Use a single, consolidated tracking file
        filename = "price_tracking.csv"
        filepath = EXPORT_DIR / filename
        
        # Create new row with current data
        new_row = {
            'timestamp': current_data['timestamp'],
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'symbol': symbol,
            'price': current_data['price'],
            'open': current_data['open'],
            'high': current_data['high'],
            'low': current_data['low'],
            'previous_close': current_data['previous_close'],
            'change': current_data['change'],
            'change_percent': current_data['change_percent']
        }
        
        # Check if file exists
        if filepath.exists():
            # Read existing data
            try:
                existing_df = pd.read_csv(filepath)
                # Check if we already have a recent entry for this symbol (avoid duplicates)
                recent_entries = existing_df[
                    (existing_df['symbol'] == symbol) & 
                    (existing_df['timestamp'] == current_data['timestamp'])
                ]
                
                if len(recent_entries) == 0:
                    # Add new row if not duplicate
                    new_df = pd.concat([existing_df, pd.DataFrame([new_row])], ignore_index=True)
                    # Sort by timestamp
                    new_df = new_df.sort_values(['symbol', 'timestamp'])
                    new_df.to_csv(filepath, index=False)
                    return True
                else:
                    return False  # Duplicate, not saved
            except Exception as e:
                logging.warning(f"Error reading existing tracking file: {e}")
                # Create new file with current data
                pd.DataFrame([new_row]).to_csv(filepath, index=False)
                return True
        else:
            # Create new file
            pd.DataFrame([new_row]).to_csv(filepath, index=False)
            return True
            
    except Exception as e:
        logging.error(f"Error saving price tracking data: {e}")
        return False


def get_tracked_historical_data(symbol, days_back=30):
    """Get accumulated historical data from the single price tracking file."""
    try:
        # Read the consolidated tracking file
        filename = "price_tracking.csv"
        filepath = EXPORT_DIR / filename
        
        if not filepath.exists():
            return {
                'success': False,
                'dates': [],
                'prices': [],
                'data_points': 0,
                'message': f'No tracked historical data found for {symbol}'
            }
            
        # Read the data and filter by symbol
        df = pd.read_csv(filepath)
        symbol_data = df[df['symbol'] == symbol].copy() # Use .copy() to avoid SettingWithCopyWarning
        
        if len(symbol_data) > 0:
            # Sort by timestamp and remove duplicates
            symbol_data = symbol_data.sort_values('timestamp').drop_duplicates(subset=['timestamp', 'symbol'])
            
            # Format for charts
            dates = symbol_data['timestamp'].tolist()
            prices = symbol_data['price'].tolist()
            
            return {
                'success': True,
                'dates': dates,
                'prices': prices,
                'data_points': len(dates),
                'message': f'Found {len(dates)} tracked data points for {symbol}'
            }
        else:
            return {
                'success': False,
                'dates': [],
                'prices': [],
                'data_points': 0,
                'message': f'No tracked historical data found for {symbol}'
            }
            
    except Exception as e:
        logging.error(f"Error getting tracked historical data: {e}")
        return {
            'success': False,
            'dates': [],
            'prices': [],
            'data_points': 0,
            'message': f'Error loading tracked data: {str(e)}'
        } 