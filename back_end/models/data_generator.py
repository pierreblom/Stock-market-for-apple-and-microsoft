import logging
import random
import math
from datetime import datetime, timedelta
from ..config import EXPORT_DIR
import pandas as pd


def calculate_data_limit(period):
    """Calculate the number of days to fetch based on the period"""
    if period == 'today':
        return 1
    elif period == '5days':
        return 5
    elif period == 'month':
        return 30
    elif period == 'year':
        return 252  # Approximate trading days in a year
    else:
        return 121  # Default


def generate_hourly_data_for_today(symbol):
    """Generate realistic hourly stock data for today (European market hours)"""
    try:
        # European market hours: 9:00 AM to 5:30 PM CET (8.5 hours)
        # Generate data every 30 minutes for smoother curves
        market_open = 9.0   # 9:00 AM CET
        market_close = 17.5 # 5:30 PM CET
        intervals_per_hour = 2  # Every 30 minutes
        total_intervals = int((market_close - market_open) * intervals_per_hour)
        
        # Get base configuration for European stocks
        stock_configs = {
            # Dutch stocks (AEX)
            'ASML.AS': {'base_price': 650, 'sector': 'tech', 'beta': 1.3, 'volatility': 0.030},
            'INGA.AS': {'base_price': 13, 'sector': 'finance', 'beta': 1.1, 'volatility': 0.025},
            'HEIA.AS': {'base_price': 85, 'sector': 'consumer', 'beta': 0.8, 'volatility': 0.020},
            'PHIA.AS': {'base_price': 25, 'sector': 'tech', 'beta': 1.0, 'volatility': 0.025},
            
            # Other European stocks
            'SAP': {'base_price': 120, 'sector': 'tech', 'beta': 1.1, 'volatility': 0.022},
            'LVMH.PA': {'base_price': 750, 'sector': 'luxury', 'beta': 0.9, 'volatility': 0.028},
            
            # Still support US stocks for comparison
            'AAPL': {'base_price': 200, 'sector': 'tech', 'beta': 1.2, 'volatility': 0.025},
            'MSFT': {'base_price': 480, 'sector': 'tech', 'beta': 1.1, 'volatility': 0.022},
            'GOOGL': {'base_price': 2800, 'sector': 'tech', 'beta': 1.3, 'volatility': 0.028},
            'TSLA': {'base_price': 350, 'sector': 'auto', 'beta': 1.8, 'volatility': 0.045}
        }
        
        # Clean symbol (remove exchange suffix for lookup)
        clean_symbol = symbol.split('.')[0] if '.' in symbol else symbol
        config = stock_configs.get(symbol, stock_configs.get(clean_symbol, stock_configs['ASML.AS']))
        
        # Start with yesterday's closing price (simulate market open)
        current_price = config['base_price'] * random.uniform(0.98, 1.02)  # ±2% gap
        
        records = []
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Generate intraday price movements
        for i in range(total_intervals):
            # Calculate time for this interval
            hours_from_open = i / intervals_per_hour
            current_hour = market_open + hours_from_open
            
            # Convert to actual time
            hour = int(current_hour)
            minute = int((current_hour - hour) * 60)
            time_str = f"{hour:02d}:{minute:02d}:00"
            timestamp = f"{today}T{time_str}"
            
            # European market factors affecting price movement
            
            # 1. Time-of-day effects (European pattern)
            time_factor = 0
            if current_hour < 10.0:  # Opening hour volatility
                time_factor = random.uniform(-0.008, 0.008)
            elif current_hour > 16.5:  # Closing hour volatility
                time_factor = random.uniform(-0.006, 0.006)
            elif 12.0 <= current_hour <= 13.0:  # Lunch hour (lower activity in Europe)
                time_factor = random.uniform(-0.002, 0.002)
            else:  # Normal trading hours
                time_factor = random.uniform(-0.004, 0.004)
            
            # 2. Random walk with mean reversion
            random_factor = random.gauss(0, config['volatility'] / 8)  # Smaller moves for intraday
            
            # 3. European trend factor
            trend_factor = math.sin(hours_from_open * math.pi / 8.5) * 0.002  # Gentle intraday trend
            
            # 4. Volume-based movement
            volume_factor = random.uniform(0.5, 2.0)
            
            # Combine all factors
            total_change = (time_factor + random_factor + trend_factor) * volume_factor
            
            # Apply change
            current_price = current_price * (1 + total_change)
            
            # Keep price within reasonable bounds (±5% from start of day)
            start_price = config['base_price']
            min_price = start_price * 0.95
            max_price = start_price * 1.05
            current_price = max(min_price, min(max_price, current_price))
            
            # Generate OHLC data for this interval
            volatility_range = current_price * config['volatility'] / 10  # Small intraday range
            
            high = current_price + random.uniform(0, volatility_range)
            low = current_price - random.uniform(0, volatility_range)
            open_price = records[-1]['close'] if records else current_price
            close_price = current_price
            
            # Generate realistic volume (European patterns)
            base_volumes = {
                'ASML.AS': 2000000,  # High volume Dutch tech stock
                'INGA.AS': 8000000,  # High volume bank
                'HEIA.AS': 1500000,  # Medium volume consumer stock
                'PHIA.AS': 3000000,  # Medium volume tech
                'SAP': 1800000,      # German software
                'LVMH.PA': 800000    # French luxury (lower volume)
            }
            
            base_volume = base_volumes.get(symbol, 1000000)
            if current_hour < 10.0 or current_hour > 16.5:
                volume = int(base_volume * random.uniform(1.5, 2.5))  # Higher volume at open/close
            elif 12.0 <= current_hour <= 13.0:
                volume = int(base_volume * random.uniform(0.3, 0.7))  # Lower during lunch
            else:
                volume = int(base_volume * random.uniform(0.7, 1.3))  # Normal volume
            
            record = {
                'date': timestamp,
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close_price, 2),
                'volume': volume
            }
            
            records.append(record)
        
        return {
            'success': True,
            'data': records,
            'message': f'Generated {len(records)} hourly data points for {symbol} today (European market simulation - CET timezone)'
        }
        
    except Exception as e:
        logging.error(f"Error generating hourly data for {symbol}: {e}")
        return {
            'success': False,
            'data': [],
            'message': f'Error generating hourly data: {str(e)}'
        }


def generate_hourly_data_for_yesterday(symbol):
    """Generate realistic hourly stock data for yesterday (European market hours)"""
    try:
        # This is largely the same as the function for today, just with the date adjusted
        market_open = 9.0
        market_close = 17.5
        intervals_per_hour = 2
        total_intervals = int((market_close - market_open) * intervals_per_hour)
        
        stock_configs = {
            'ASML.AS': {'base_price': 650, 'sector': 'tech', 'beta': 1.3, 'volatility': 0.030},
            'INGA.AS': {'base_price': 13, 'sector': 'finance', 'beta': 1.1, 'volatility': 0.025},
            'HEIA.AS': {'base_price': 85, 'sector': 'consumer', 'beta': 0.8, 'volatility': 0.020},
            'PHIA.AS': {'base_price': 25, 'sector': 'tech', 'beta': 1.0, 'volatility': 0.025},
            'SAP': {'base_price': 120, 'sector': 'tech', 'beta': 1.1, 'volatility': 0.022},
            'LVMH.PA': {'base_price': 750, 'sector': 'luxury', 'beta': 0.9, 'volatility': 0.028},
            'AAPL': {'base_price': 200, 'sector': 'tech', 'beta': 1.2, 'volatility': 0.025},
            'MSFT': {'base_price': 480, 'sector': 'tech', 'beta': 1.1, 'volatility': 0.022},
            'GOOGL': {'base_price': 2800, 'sector': 'tech', 'beta': 1.3, 'volatility': 0.028},
            'TSLA': {'base_price': 350, 'sector': 'auto', 'beta': 1.8, 'volatility': 0.045}
        }
        
        clean_symbol = symbol.split('.')[0] if '.' in symbol else symbol
        config = stock_configs.get(symbol, stock_configs.get(clean_symbol, stock_configs['ASML.AS']))
        
        current_price = config['base_price'] * random.uniform(0.98, 1.02)
        records = []
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        for i in range(total_intervals):
            hours_from_open = i / intervals_per_hour
            current_hour = market_open + hours_from_open
            
            hour = int(current_hour)
            minute = int((current_hour - hour) * 60)
            time_str = f"{hour:02d}:{minute:02d}:00"
            timestamp = f"{yesterday}T{time_str}"
            
            time_factor = random.uniform(-0.004, 0.004)
            random_factor = random.gauss(0, config['volatility'] / 8)
            trend_factor = math.sin(hours_from_open * math.pi / 8.5) * 0.002
            total_change = time_factor + random_factor + trend_factor
            
            current_price = current_price * (1 + total_change)
            
            volatility_range = current_price * config['volatility'] / 10
            high = current_price + random.uniform(0, volatility_range)
            low = current_price - random.uniform(0, volatility_range)
            open_price = records[-1]['close'] if records else current_price
            close_price = current_price
            
            base_volume = 1000000
            volume = int(base_volume * random.uniform(0.7, 1.3))
            
            record = {
                'date': timestamp,
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close_price, 2),
                'volume': volume
            }
            records.append(record)
        
        return {
            'success': True,
            'data': records,
            'message': f'Generated {len(records)} hourly data points for {symbol} yesterday (simulation)'
        }
        
    except Exception as e:
        logging.error(f"Error generating hourly data for {symbol} yesterday: {e}")
        return {
            'success': False,
            'data': [],
            'message': f'Error generating hourly data for yesterday: {str(e)}'
        }


def filter_data_by_month(records, month_year):
    """Filter records to only include data from the specified month/year"""
    if not month_year or not records:
        return records
    
    try:
        # Parse the month/year string (e.g., "June 2024")
        month_date = datetime.strptime(month_year, '%B %Y')
        target_month = month_date.month
        target_year = month_date.year
        
        filtered_records = []
        for record in records:
            if 'date' in record:
                try:
                    record_date = datetime.strptime(record['date'].split('T')[0], '%Y-%m-%d')
                    if record_date.month == target_month and record_date.year == target_year:
                        filtered_records.append(record)
                except (ValueError, AttributeError):
                    continue
        
        return filtered_records
    except ValueError:
        # If month_year format is invalid, return original records
        return records


def get_todays_real_data(symbol):
    """Get real tracking data for today from the consolidated tracking file."""
    try:
        # Use the single, consolidated tracking file
        filename = "price_tracking.csv"
        filepath = EXPORT_DIR / filename
        
        if not filepath.exists():
            return {
                'success': False,
                'data': [],
                'message': 'No real tracking data file found.'
            }
        
        # Read tracking data
        df = pd.read_csv(filepath)
        # Filter out NaN values in symbol column first
        df = df.dropna(subset=['symbol'])

        # Filter for today's data
        today_str = datetime.now().strftime('%Y-%m-%d')
        symbol_data = df[(df['symbol'] == symbol.upper()) & (df['date'] == today_str)]
        
        if len(symbol_data) == 0:
            return {
                'success': False,
                'data': [],
                'message': f'No real data found for {symbol} in today\'s tracking file'
            }
        
        # Sort by timestamp 
        symbol_data = symbol_data.copy()
        symbol_data['timestamp_dt'] = pd.to_datetime(symbol_data['timestamp'])
        symbol_data = symbol_data.sort_values('timestamp_dt')
        
        # Convert to expected format
        records = []
        for _, row in symbol_data.iterrows():
            record = {
                'date': row['timestamp'],  # Keep full timestamp for today data
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['price']),  # Use current price as close
                'volume': 1000000  # Default volume since tracking doesn't store volume
            }
            records.append(record)
        
        return {
            'success': True,
            'data': records,
            'message': f'Using {len(records)} real tracking data points for {symbol} today'
        }
        
    except Exception as e:
        logging.error(f"Error reading today's real data for {symbol}: {e}")
        return {
            'success': False,
            'data': [],
            'message': f'Error reading real data for today: {str(e)}'
        }


def get_yesterdays_real_data(symbol):
    """Get real tracking data for yesterday from the consolidated tracking file."""
    try:
        # Use the single, consolidated tracking file
        filename = "price_tracking.csv"
        filepath = EXPORT_DIR / filename
        
        if not filepath.exists():
            return {
                'success': False,
                'data': [],
                'message': 'No real tracking data file found.'
            }
        
        # Read tracking data
        df = pd.read_csv(filepath)
        df = df.dropna(subset=['symbol'])

        # Filter for yesterday's data
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        symbol_data = df[(df['symbol'] == symbol.upper()) & (df['date'] == yesterday_str)]
        
        if len(symbol_data) == 0:
            return {
                'success': False,
                'data': [],
                'message': f'No real data found for {symbol} in yesterday\'s tracking file'
            }
        
        # Sort by timestamp 
        symbol_data = symbol_data.copy()
        symbol_data['timestamp_dt'] = pd.to_datetime(symbol_data['timestamp'])
        symbol_data = symbol_data.sort_values('timestamp_dt')
        
        # Convert to expected format
        records = []
        for _, row in symbol_data.iterrows():
            record = {
                'date': row['timestamp'],
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['price']),
                'volume': 1000000
            }
            records.append(record)
        
        return {
            'success': True,
            'data': records,
            'message': f'Using {len(records)} real tracking data points for {symbol} from yesterday'
        }
        
    except Exception as e:
        logging.error(f"Error reading yesterday's real data for {symbol}: {e}")
        return {
            'success': False,
            'data': [],
            'message': f'Error reading real data for yesterday: {str(e)}'
        } 