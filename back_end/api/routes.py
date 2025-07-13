from flask import Blueprint, jsonify, request, send_file, send_from_directory, abort, Response
import pandas as pd
import numpy as np
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Import our modules
from ..config import FINNHUB_API_KEY, AUTO_DOWNLOAD_SYMBOLS, EXPORT_DIR, API_TIMEOUT
from .. import config
from ..models.data_fetcher import MarketDataFetcher
from ..models.database import save_to_database_csv, load_from_database_csv, update_database_from_tracking
from ..models.data_generator import (
    calculate_data_limit, 
    filter_data_by_month,
    get_todays_real_data,
    get_yesterdays_real_data
)
from ..services.tracking import save_price_tracking_data, get_tracked_historical_data
from ..services.scheduler import automated_daily_download
from ..utils.helpers import cleanup_duplicate_csv_files

# Create Blueprint
api = Blueprint('api', __name__)


@api.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Check if API key is configured
        api_key_configured = bool(FINNHUB_API_KEY and FINNHUB_API_KEY.strip() != '')
        
        return jsonify({
            'status': 'healthy',
            'message': 'Stock dashboard is running',
            'config': {
                'api_key_configured': api_key_configured,
                'api_timeout': f"{API_TIMEOUT}s"
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Health check failed: {str(e)}'
        }), 500


@api.route('/stock_data/<symbol>')
def get_stock_data(symbol):
    """Get stock data from the database or generate it"""
    try:
        # Fetch latest data and save it for tracking
        fetcher = MarketDataFetcher()
        current_data_result = fetcher.get_current_data(symbol.upper())
        if current_data_result['success']:
            save_price_tracking_data(symbol.upper(), current_data_result['data'])
            
        period = request.args.get('period', 'default')
        
        # Handle time-based periods (Today, Yesterday)
        if period in ['today', 'yesterday']:
            historical_result = None
            if period == 'today':
                historical_result = get_todays_real_data(symbol.upper())
                # Fallback to simulation if no real data
                # if not historical_result['success']:
                #     historical_result = generate_hourly_data_for_today(symbol.upper())
            elif period == 'yesterday':
                historical_result = get_yesterdays_real_data(symbol.upper())
                # if not historical_result['success']:
                #     historical_result = generate_hourly_data_for_yesterday(symbol.upper())
            
            records_to_process = historical_result['data'] if historical_result and historical_result['success'] else []
            
            # Use full timestamp for hourly data
            dates = [r['date'] for r in records_to_process]
            prices = [float(r['close']) for r in records_to_process]
            volumes = [int(r.get('volume', 0)) for r in records_to_process]
            
            # Fetch the latest available record from the main database for the 'current' card
            db_load_result = load_from_database_csv(symbol.upper())
            current_data = None
            if db_load_result['success'] and db_load_result['data']:
                all_records = sorted(db_load_result['data'], key=lambda r: r['date'])
                last_record = all_records[-1]
                previous_close = all_records[-2]['close'] if len(all_records) > 1 else last_record['open']
                change = float(last_record['close']) - float(previous_close)
                change_percent = (change / float(previous_close)) * 100 if float(previous_close) != 0 else 0
                
                current_data = {
                    'price': float(last_record['close']),
                    'high': float(last_record['high']),
                    'low': float(last_record['low']),
                    'open': float(last_record['open']),
                    'previous_close': float(previous_close),
                    'change': change,
                    'change_percent': change_percent,
                    'timestamp': last_record['date'].split('T')[0]
                }

            return jsonify({
                'success': True, 'symbol': symbol.upper(), 'dates': dates, 'prices': prices,
                'volumes': volumes, 'current': current_data, 'errors': [],
                'messages': {'historical': historical_result['message'], 'current': 'From database.'},
                'granularity': 'hourly'
            })

        # Handle date-based periods (Week, Month, All)
        db_load_result = load_from_database_csv(symbol.upper())
        
        if not db_load_result['success']:
            return jsonify({
                'success': True, 'symbol': symbol.upper(), 'dates': [], 'prices': [],
                'volumes': [], 'current': None, 'errors': [db_load_result['message']],
                'messages': {'historical': 'No data found in database.', 'current': ''}
            })

        all_records = db_load_result['data']
        for r in all_records:
            try:
                r['date_obj'] = datetime.strptime(r['date'].split('T')[0], '%Y-%m-%d')
            except (ValueError, KeyError):
                continue
        
        all_records = [r for r in all_records if 'date_obj' in r]
        all_records.sort(key=lambda r: r['date_obj'])
        
        if all_records:
            today = all_records[-1]['date_obj']
        else:
            today = datetime.now()
        
        records_to_process = []
        if period == 'week':
            today_date = today.date()
            # Calculate the start of the previous week (Monday)
            start_of_last_week = today_date - timedelta(days=today_date.weekday() + 7)
            # Calculate the end of the previous week (Friday)
            end_of_last_week = start_of_last_week + timedelta(days=4)
            
            records_to_process = [
                r for r in all_records 
                if start_of_last_week <= r['date_obj'].date() <= end_of_last_week
            ]
        elif period == 'month':
            today_date = today.date()
            first_day_current_month = today_date.replace(day=1)
            end_of_last_month = first_day_current_month - timedelta(days=1)
            start_of_last_month = end_of_last_month.replace(day=1)
            
            records_to_process = [
                r for r in all_records 
                if start_of_last_month <= r['date_obj'].date() <= end_of_last_month
            ]
        else:
            records_to_process = all_records

        dates = [r['date_obj'].strftime('%Y-%m-%d') for r in records_to_process]
        prices = [float(r['close']) for r in records_to_process]
        volumes = [int(r.get('volume', 0)) for r in records_to_process]
        
        current_data = None
        if all_records:
            last_record = all_records[-1]
            previous_close = all_records[-2]['close'] if len(all_records) > 1 else last_record['open']
            change = float(last_record['close']) - float(previous_close)
            change_percent = (change / float(previous_close)) * 100 if float(previous_close) != 0 else 0
            
            current_data = {
                'price': float(last_record['close']),
                'high': float(last_record['high']),
                'low': float(last_record['low']),
                'open': float(last_record['open']),
                'previous_close': float(previous_close),
                'change': change,
                'change_percent': change_percent,
                'timestamp': last_record['date_obj'].strftime('%Y-%m-%d')
            }

        return jsonify({
            'success': True, 'symbol': symbol.upper(), 'dates': dates, 'prices': prices,
            'volumes': volumes, 'current': current_data, 'errors': [],
            'messages': {'historical': f"Loaded {len(records_to_process)} records from database.", 'current': 'From database.'},
            'granularity': 'daily'
        })
        
    except Exception as e:
        logging.error(f"Error in get_stock_data: {e}")
        return jsonify({
            'success': False, 'symbol': symbol.upper(), 'dates': [], 'prices': [],
            'volumes': [], 'current': None, 'errors': [f'Server error: {str(e)}'],
            'messages': {}
        }), 500


@api.route('/comparison_data')
def get_comparison_data():
    """Get comparison data for multiple symbols"""
    try:
        symbols_str = request.args.get('symbols', 'NVDA,MSFT')
        symbols = [s.strip().upper() for s in symbols_str.split(',') if s.strip()]
        
        period = request.args.get('period', 'default')
        month_filter = request.args.get('month', None)
        limit = calculate_data_limit(period)
        
        fetcher = MarketDataFetcher()
        
        data = {}
        global_errors = []
        
        for symbol in symbols:
            # Special handling for "today" period - try real data first, fallback to simulation
            if period == 'today':
                # First try to get real tracking data for today
                real_data_result = get_todays_real_data(symbol)
                
                if real_data_result['success'] and real_data_result['data']:
                    # Use real tracking data
                    historical_result = real_data_result
                    logging.info(f"✅ Using REAL data for {symbol} today: {len(real_data_result['data'])} data points")
                else:
                    # Fall back to simulation if no real data
                    historical_result = {'success': False, 'data': [], 'message': 'No real data available.'}
                    logging.info(f"🎲 No data for {symbol} today (no real data found): {real_data_result['message']}")
                
                current_result = fetcher.get_current_data(symbol)
            else:
                historical_result = fetcher.get_historical_data(symbol)
                current_result = fetcher.get_current_data(symbol)
            
            dates = []
            prices = []
            errors = []
            
            # Check for errors
            if not historical_result['success']:
                errors.append(f"Historical data: {historical_result['message']}")
                global_errors.append(f"{symbol} historical: {historical_result['message']}")
            
            if not current_result['success']:
                errors.append(f"Current data: {current_result['message']}")
                global_errors.append(f"{symbol} current: {current_result['message']}")
            
            # Process data if available
            if historical_result['success'] and historical_result['data']:
                # Reverse to get chronological order (newest first)
                all_records = list(reversed(historical_result['data']))
                
                # Apply month filtering if specified
                if month_filter:
                    all_records = filter_data_by_month(all_records, month_filter)
                
                # Apply client-side filtering based on limit (BUT NOT for hourly today data)
                if period == 'today':
                    # For today period, use all hourly data points (don't limit to 1)
                    records_to_process = all_records
                else:
                    # For other periods, apply normal limit filtering
                    records_to_process = all_records[:limit] if limit < len(all_records) else all_records
                
                for record in records_to_process:
                    if 'date' in record and 'close' in record:
                        try:
                            # For today period with hourly data, preserve full timestamp for horizontal display
                            if period == 'today' and 'T' in record['date']:
                                date_str = record['date']  # Keep full timestamp (e.g., "2025-07-02T09:30:00")
                            else:
                                date_str = record['date'].split('T')[0]  # Get just the date part for daily data
                            dates.append(date_str)
                            prices.append(float(record['close']))
                        except (ValueError, KeyError):
                            continue
            
            # Success if we have current data (even if historical fails)
            has_current_data = current_result['success'] and current_result['data'] is not None
            symbol_success = has_current_data or (historical_result['success'] and len(dates) > 0)
            
            data[symbol] = {
                'success': symbol_success,
                'dates': dates,
                'prices': prices,
                'current': current_result['data'] if current_result['success'] else None,
                'errors': errors
            }
        
        # Overall success if any symbol has current data
        any_current_data = any(data[symbol]['current'] is not None for symbol in data)
        overall_success = any_current_data or len(global_errors) == 0
        
        return jsonify({
            'success': overall_success,
            'data': data,
            'errors': global_errors
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'data': {},
            'errors': [str(e)]
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'data': {},
            'errors': [f'Server error: {str(e)}']
        }), 500


@api.route('/csv/list')
def list_csv_files():
    """List all available CSV files"""
    try:
        csv_files = []
        if EXPORT_DIR.exists():
            for csv_file in EXPORT_DIR.glob("*.csv"):
                file_stats = csv_file.stat()
                csv_files.append({
                    'filename': csv_file.name,
                    'size': file_stats.st_size,
                    'created': datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                    'modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                })
        
        # Sort by modification time (newest first)
        csv_files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'success': True,
            'files': csv_files,
            'count': len(csv_files)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'files': [],
            'count': 0,
            'error': str(e)
        }), 500


@api.route('/csv/download/<filename>')
def download_csv(filename):
    """Download a specific CSV file"""
    try:
        # Security check: ensure filename doesn't contain path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            abort(400, "Invalid filename")
        
        filepath = EXPORT_DIR / filename
        
        if not filepath.exists():
            abort(404, "File not found")
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
    
    except Exception as e:
        abort(500, f"Error downloading file: {str(e)}")


@api.route('/csv/export/<symbol>')
def export_stock_data_csv(symbol):
    """Export current stock data to CSV and download immediately"""
    try:
        fetcher = MarketDataFetcher()
        
        # Get period and month from query parameters
        period = request.args.get('period', 'all')
        month_filter = request.args.get('month', None)
        limit = calculate_data_limit(period) if period != 'all' else None
        
        # Get historical data
        historical_result = fetcher.get_historical_data(symbol.upper(), limit)
        
        if not historical_result['success'] or not historical_result['data']:
            return jsonify({
                'success': False,
                'message': f"No data available for {symbol.upper()}: {historical_result['message']}"
            }), 404
        
        # Process data
        all_records = list(reversed(historical_result['data']))
        
        # Apply month filtering if specified
        if month_filter:
            all_records = filter_data_by_month(all_records, month_filter)
        
        # Apply client-side filtering based on limit
        records_to_export = all_records[:limit] if limit and limit < len(all_records) else all_records
        
        if not records_to_export:
            return jsonify({
                'success': False,
                'message': f"No data available for the specified period"
            }), 404
        
        # Save to CSV
        csv_result = save_to_database_csv(records_to_export, symbol.upper())
        
        if not csv_result or not csv_result['success']:
            return jsonify({
                'success': False,
                'message': "Failed to create CSV file"
            }), 500
        
        # Return the file for download
        return send_file(
            csv_result['filepath'],
            as_attachment=True,
            download_name=csv_result['filename'],
            mimetype='text/csv'
        )
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error exporting data: {str(e)}"
        }), 500


@api.route('/auto-download/trigger')
def trigger_auto_download():
    """Manually trigger the automated download process"""
    try:
        results = automated_daily_download()
        
        successful = sum(1 for r in results.values() if r['success'])
        total_symbols = len(results)
        total_records = sum(r['records'] for r in results.values())
        
        return jsonify({
            'success': True,
            'message': f'Download triggered successfully: {successful}/{total_symbols} symbols processed',
            'results': results,
            'summary': {
                'successful_symbols': successful,
                'total_symbols': total_symbols,
                'total_records': total_records
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error triggering download: {str(e)}",
            'results': {}
        }), 500


@api.route('/auto-download/status')
def auto_download_status():
    """Get status of automatic download configuration"""
    try:
        from ..config import AUTO_DOWNLOAD_ENABLED, DAILY_UPDATE_HOUR, DAILY_UPDATE_MINUTE
        
        return jsonify({
            'success': True,
            'config': {
                'enabled': AUTO_DOWNLOAD_ENABLED,
                'hour': DAILY_UPDATE_HOUR,
                'minute': DAILY_UPDATE_MINUTE,
                'symbols': AUTO_DOWNLOAD_SYMBOLS,
                'api_key_configured': bool(FINNHUB_API_KEY)
            },
            'next_run': f"{DAILY_UPDATE_HOUR:02d}:{DAILY_UPDATE_MINUTE:02d} daily"
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error getting status: {str(e)}"
        }), 500


@api.route('/market/correlation')
def get_market_correlation():
    """Advanced market correlation analysis"""
    try:
        symbols = request.args.get('symbols', 'AAPL,MSFT,GOOGL').split(',')
        period = request.args.get('period', 'default')
        
        fetcher = MarketDataFetcher()
        correlation_data = {}
        stock_returns = {}
        
        # Get data for all symbols
        for symbol in symbols[:10]:  # Limit to 10 symbols
            symbol = symbol.strip().upper()
            result = fetcher.get_historical_data(symbol, 60)
            
            if result['success'] and result['data']:
                prices = [float(record['close']) for record in result['data']]
                # Calculate daily returns
                returns = [(prices[i] - prices[i+1]) / prices[i+1] for i in range(len(prices)-1)]
                stock_returns[symbol] = returns
        
        # Calculate correlation matrix
        correlation_matrix = {}
        symbols_list = list(stock_returns.keys())
        
        for i, symbol1 in enumerate(symbols_list):
            correlation_matrix[symbol1] = {}
            for j, symbol2 in enumerate(symbols_list):
                if len(stock_returns[symbol1]) > 0 and len(stock_returns[symbol2]) > 0:
                    min_length = min(len(stock_returns[symbol1]), len(stock_returns[symbol2]))
                    returns1 = stock_returns[symbol1][:min_length]
                    returns2 = stock_returns[symbol2][:min_length]
                    
                    if len(returns1) > 1:
                        correlation = np.corrcoef(returns1, returns2)[0, 1]
                        correlation_matrix[symbol1][symbol2] = round(float(correlation), 3)
                    else:
                        correlation_matrix[symbol1][symbol2] = 0.0
                else:
                    correlation_matrix[symbol1][symbol2] = 0.0
        
        # Calculate market metrics
        market_volatility = {}
        for symbol in symbols_list:
            if len(stock_returns[symbol]) > 0:
                volatility = np.std(stock_returns[symbol]) * (252**0.5)  # Annualized
                market_volatility[symbol] = round(float(volatility), 3)
        
        return jsonify({
            'success': True,
            'correlation_matrix': correlation_matrix,
            'market_volatility': market_volatility,
            'symbols': symbols_list,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': f'Correlation analysis complete for {len(symbols_list)} symbols'
        })
        
    except Exception as e:
        logging.error(f"Correlation analysis failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Correlation analysis failed: {str(e)}',
            'correlation_matrix': {},
            'market_volatility': {}
        }), 500


@api.route('/market/events')
def get_market_events():
    """Detect significant market events from price movements"""
    try:
        symbol = request.args.get('symbol', 'AAPL').upper()
        threshold = float(request.args.get('threshold', '0.05'))  # 5% default
        
        fetcher = MarketDataFetcher()
        result = fetcher.get_historical_data(symbol, 60)
        
        if not result['success'] or not result['data']:
            return jsonify({
                'success': False,
                'message': f'No data available for {symbol}',
                'events': []
            })
        
        events = []
        data = result['data']
        
        for i in range(1, len(data)):
            prev_close = float(data[i-1]['close'])
            curr_close = float(data[i]['close'])
            daily_return = (curr_close - prev_close) / prev_close
            
            if abs(daily_return) >= threshold:
                event_type = "Large Move Up" if daily_return > 0 else "Large Move Down"
                magnitude = "Extreme" if abs(daily_return) > threshold * 2 else "Significant"
                
                events.append({
                    'date': data[i]['date'],
                    'type': event_type,
                    'magnitude': magnitude,
                    'return': round(daily_return * 100, 2),
                    'price_from': round(prev_close, 2),
                    'price_to': round(curr_close, 2),
                    'volume': data[i]['volume']
                })
        
        # Sort by date (most recent first)
        events.sort(key=lambda x: x['date'], reverse=True)
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'threshold': threshold * 100,
            'events': events[:20],  # Return most recent 20 events
            'total_events': len(events),
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        logging.error(f"Event detection failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Event detection failed: {str(e)}',
            'events': []
        }), 500


@api.route('/cleanup')
def trigger_cleanup():
    """Manual cleanup trigger for duplicate files"""
    result = cleanup_duplicate_csv_files()
    return jsonify({
        'success': True,
        'message': f"Cleanup complete: Deleted {result['deleted']} duplicates, kept {result['kept']} files",
        'deleted': result['deleted'],
        'kept': result['kept']
    })


@api.route('/database/save/<symbol>')
def save_to_database(symbol):
    """Explicitly save current stock data to CSV database"""
    try:
        fetcher = MarketDataFetcher()
        
        # Get fresh data
        historical_result = fetcher.get_historical_data(symbol.upper(), 60)
        
        if not historical_result['success'] or not historical_result['data']:
            return jsonify({
                'success': False,
                'message': f"No data available to save for {symbol.upper()}: {historical_result['message']}"
            }), 404
        
        # Save to database
        db_result = save_to_database_csv(historical_result['data'], symbol.upper())
        
        return jsonify({
            'success': db_result['success'],
            'symbol': symbol.upper(),
            'message': db_result['message'],
            'records_added': db_result['records'],
            'total_records': db_result['total_records'],
            'updated': db_result['updated'],
            'filename': db_result['filename']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error saving to database: {str(e)}"
        }), 500


@api.route('/database/load/<symbol>')
def load_from_database(symbol):
    """Load stock data from CSV database"""
    try:
        # Try to load from database first
        db_result = load_from_database_csv(symbol.upper())
        
        if db_result['success'] and db_result['data']:
            # Process database data for chart format
            dates = []
            prices = []
            volumes = []
            
            for record in db_result['data']:
                if 'date' in record and 'close' in record:
                    try:
                        date_str = record['date'].split('T')[0]
                        dates.append(date_str)
                        prices.append(float(record['close']))
                        volumes.append(int(record.get('volume', 0)))
                    except (ValueError, KeyError):
                        continue
            
            return jsonify({
                'success': True,
                'symbol': symbol.upper(),
                'dates': dates,
                'prices': prices,
                'volumes': volumes,
                'source': 'database',
                'records': len(dates),
                'message': f'Loaded from database: {db_result["filename"]}',
                'filename': db_result['filename']
            })
        else:
            return jsonify({
                'success': False,
                'symbol': symbol.upper(),
                'dates': [],
                'prices': [],
                'volumes': [],
                'source': 'database',
                'records': 0,
                'message': db_result['message']
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error loading from database: {str(e)}"
        }), 500


@api.route('/database/list')
def list_database_files():
    """List all available CSV database files"""
    try:
        database_files = list(EXPORT_DIR.glob("*_database.csv"))
        
        files_info = []
        for filepath in database_files:
            try:
                df = pd.read_csv(filepath)
                symbol = filepath.stem.replace('_database', '').upper()
                
                files_info.append({
                    'symbol': symbol,
                    'filename': filepath.name,
                    'records': len(df),
                    'size_kb': round(filepath.stat().st_size / 1024, 1),
                    'last_modified': filepath.stat().st_mtime,
                    'date_range': {
                        'earliest': df['date'].min() if 'date' in df.columns else None,
                        'latest': df['date'].max() if 'date' in df.columns else None
                    }
                })
            except Exception as e:
                files_info.append({
                    'symbol': 'UNKNOWN',
                    'filename': filepath.name,
                    'records': 0,
                    'size_kb': 0,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'databases': files_info,
            'total_files': len(files_info),
            'message': f'Found {len(files_info)} database files'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'databases': [],
            'message': f"Error listing databases: {str(e)}"
        }), 500


@api.route('/database/update-all')
def update_all_databases():
    """Update all database files with fresh data"""
    try:
        fetcher = MarketDataFetcher()
        symbols = ['NVDA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']  # Add more as needed
        results = {}
        
        for symbol in symbols:
            try:
                # Get fresh data
                historical_result = fetcher.get_historical_data(symbol, 60)
                
                if historical_result['success'] and historical_result['data']:
                    # Update database
                    db_result = save_to_database_csv(historical_result['data'], symbol)
                    results[symbol] = {
                        'success': db_result['success'],
                        'message': db_result['message'],
                        'records_added': db_result['records'],
                        'total_records': db_result['total_records'],
                        'updated': db_result['updated']
                    }
                else:
                    results[symbol] = {
                        'success': False,
                        'message': historical_result['message'],
                        'records_added': 0,
                        'total_records': 0,
                        'updated': False
                    }
                    
            except Exception as e:
                results[symbol] = {
                    'success': False,
                    'message': str(e),
                    'records_added': 0,
                    'total_records': 0,
                    'updated': False
                }
        
        successful = sum(1 for r in results.values() if r['success'])
        total_records = sum(r['total_records'] for r in results.values())
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'successful_symbols': successful,
                'total_symbols': len(symbols),
                'total_records': total_records
            },
            'message': f'Updated {successful}/{len(symbols)} databases with {total_records} total records'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error updating databases: {str(e)}"
        }), 500


@api.route('/database/update-from-tracking', methods=['POST'])
def update_from_tracking():
    """Update database files from the real-time tracking file."""
    try:
        result = update_database_from_tracking()
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error in update_from_tracking endpoint: {e}")
        return jsonify({
            'success': False,
            'message': f"A server error occurred: {str(e)}"
        }), 500


@api.route('/today/real-data')
def show_todays_real_data():
    """Show what real tracking data is available for today from the consolidated file."""
    try:
        filename = "price_tracking.csv"
        filepath = EXPORT_DIR / filename
        
        if not filepath.exists():
            return jsonify({
                'success': False,
                'message': 'No tracking file found.',
                'filename': filename,
                'symbols': [],
                'data_points': {}
            })
        
        # Read the tracking file
        df = pd.read_csv(filepath)
        # Filter out NaN values in symbol column first
        df = df.dropna(subset=['symbol'])
        
        # Filter for today's data
        today_str = datetime.now().strftime('%Y-%m-%d')
        today_df = df[df['date'] == today_str]

        if today_df.empty:
            return jsonify({
                'success': True,
                'message': f'Tracking file exists, but no data found for today ({today_str}).',
                'filename': filename,
                'symbols': [],
                'data_points': {}
            })

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

        return jsonify({
            'success': True,
            'message': f'Found data for {len(symbols_available)} symbols for today.',
            'filename': filename,
            'symbols': symbols_available,
            'data_points': data_points,
            'latest_data': latest_data
        })
        
    except Exception as e:
        logging.error(f"Error showing today's real data: {e}")
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}',
        }), 500 