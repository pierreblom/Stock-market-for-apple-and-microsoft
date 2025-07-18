"""
Stock service for handling stock data business logic.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from ..models.data_fetcher import MarketDataFetcher
from ..models.database import save_to_database_csv, load_from_database_csv
from ..models.data_generator import (
    calculate_data_limit, 
    filter_data_by_month,
    get_todays_real_data,
    get_yesterdays_real_data
)
from ..services.tracking import save_price_tracking_data
from ..services.technical_analysis_service import TechnicalAnalysisService
from ..services.prediction_service import PredictionService
from ..utils.exceptions import DataFetchException, DatabaseException
from ..utils.logger import get_logger, log_data_operation, log_error
from ..config import config


class StockService:
    """Service for stock data operations."""
    
    def __init__(self):
        self.fetcher = MarketDataFetcher()
        self.technical_analysis = TechnicalAnalysisService()
        self.prediction_service = PredictionService()
        self.logger = get_logger(__name__)
    
    def get_stock_data(self, symbol: str, period: str = 'default') -> Dict:
        """Get stock data for a specific symbol and period."""
        symbol = symbol.upper()
        
        self.logger.info(f"Fetching stock data for {symbol} (period: {period})")
        
        try:
            # Fetch latest data and save it for tracking
            current_data_result = self.fetcher.get_current_data(symbol)
            if current_data_result['success']:
                save_price_tracking_data(symbol, current_data_result['data'])
                log_data_operation(self.logger, "tracking_save", symbol, 1)
            
            # Handle time-based periods (Today, Yesterday)
            if period in ['today', 'yesterday']:
                return self._get_time_based_data(symbol, period)
            
            # Handle date-based periods (Week, Month, All)
            return self._get_date_based_data(symbol, period)
            
        except Exception as e:
            log_error(self.logger, e, f"get_stock_data for {symbol}")
            raise
    
    def _get_time_based_data(self, symbol: str, period: str) -> Dict:
        """Get time-based data (today/yesterday)."""
        historical_result = None
        if period == 'today':
            historical_result = get_todays_real_data(symbol)
        elif period == 'yesterday':
            historical_result = get_yesterdays_real_data(symbol)
        
        records_to_process = historical_result['data'] if historical_result and historical_result['success'] else []
        
        # Use full timestamp for hourly data
        dates = [r['date'] for r in records_to_process]
        prices = [float(r['close']) for r in records_to_process]
        volumes = [int(r.get('volume', 0)) for r in records_to_process]
        
        # Get current data from database
        current_data = self._get_current_data_from_db(symbol)
        
        return {
            'success': True,
            'symbol': symbol,
            'dates': dates,
            'prices': prices,
            'volumes': volumes,
            'current': current_data,
            'errors': [],
            'messages': {
                'historical': historical_result['message'] if historical_result else 'No data available',
                'current': 'From database.'
            },
            'granularity': 'hourly'
        }
    
    def _get_date_based_data(self, symbol: str, period: str) -> Dict:
        """Get date-based data (week/month/all)."""
        db_load_result = load_from_database_csv(symbol)
        
        if not db_load_result['success']:
            return {
                'success': True,
                'symbol': symbol,
                'dates': [],
                'prices': [],
                'volumes': [],
                'current': None,
                'errors': [db_load_result['message']],
                'messages': {'historical': 'No data found in database.', 'current': ''}
            }
        
        all_records = self._process_database_records(db_load_result['data'])
        records_to_process = self._filter_records_by_period(all_records, period)
        
        dates = [r['date_obj'].strftime('%Y-%m-%d') for r in records_to_process]
        prices = [float(r['close']) for r in records_to_process]
        volumes = [int(r.get('volume', 0)) for r in records_to_process]
        
        current_data = self._get_current_data_from_db(symbol)
        
        return {
            'success': True,
            'symbol': symbol,
            'dates': dates,
            'prices': prices,
            'volumes': volumes,
            'current': current_data,
            'errors': [],
            'messages': {
                'historical': f"Loaded {len(records_to_process)} records from database.",
                'current': 'From database.'
            },
            'granularity': 'daily'
        }
    
    def _process_database_records(self, records: List[Dict]) -> List[Dict]:
        """Process and sort database records."""
        for r in records:
            try:
                r['date_obj'] = datetime.strptime(r['date'].split('T')[0], '%Y-%m-%d')
            except (ValueError, KeyError):
                continue
        
        records = [r for r in records if 'date_obj' in r]
        records.sort(key=lambda r: r['date_obj'])
        return records
    
    def _filter_records_by_period(self, records: List[Dict], period: str) -> List[Dict]:
        """Filter records based on period."""
        if not records:
            return []
        
        today = records[-1]['date_obj']
        
        if period == 'week':
            today_date = today.date()
            start_of_last_week = today_date - timedelta(days=today_date.weekday() + 7)
            end_of_last_week = start_of_last_week + timedelta(days=4)
            
            return [
                r for r in records 
                if start_of_last_week <= r['date_obj'].date() <= end_of_last_week
            ]
        elif period == 'month':
            today_date = today.date()
            first_day_current_month = today_date.replace(day=1)
            end_of_last_month = first_day_current_month - timedelta(days=1)
            start_of_last_month = end_of_last_month.replace(day=1)
            
            return [
                r for r in records 
                if start_of_last_month <= r['date_obj'].date() <= end_of_last_month
            ]
        else:
            return records
    
    def _get_current_data_from_db(self, symbol: str) -> Optional[Dict]:
        """Get current data from database."""
        db_load_result = load_from_database_csv(symbol)
        if not db_load_result['success'] or not db_load_result['data']:
            return None
        
        all_records = sorted(db_load_result['data'], key=lambda r: r['date'])
        if len(all_records) < 2:
            return None
        
        last_record = all_records[-1]
        previous_close = all_records[-2]['close']
        change = float(last_record['close']) - float(previous_close)
        change_percent = (change / float(previous_close)) * 100 if float(previous_close) != 0 else 0
        
        return {
            'price': float(last_record['close']),
            'high': float(last_record['high']),
            'low': float(last_record['low']),
            'open': float(last_record['open']),
            'previous_close': float(previous_close),
            'change': change,
            'change_percent': change_percent,
            'timestamp': last_record['date'].split('T')[0]
        }
    
    def get_comparison_data(self, symbols: List[str], period: str = 'default', month_filter: Optional[str] = None) -> Dict:
        """Get comparison data for multiple symbols."""
        data = {}
        global_errors = []
        
        for symbol in symbols:
            symbol = symbol.strip().upper()
            
            # Special handling for "today" period
            if period == 'today':
                real_data_result = get_todays_real_data(symbol)
                if real_data_result['success'] and real_data_result['data']:
                    historical_result = real_data_result
                    logging.info(f"✅ Using REAL data for {symbol} today: {len(real_data_result['data'])} data points")
                else:
                    historical_result = {'success': False, 'data': [], 'message': 'No real data available.'}
                    logging.info(f"🎲 No data for {symbol} today (no real data found): {real_data_result['message']}")
            else:
                historical_result = self.fetcher.get_historical_data(symbol)
            
            current_result = self.fetcher.get_current_data(symbol)
            
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
                all_records = list(reversed(historical_result['data']))
                
                # Apply month filtering if specified
                if month_filter:
                    all_records = filter_data_by_month(all_records, month_filter)
                
                # Apply limit filtering
                limit = calculate_data_limit(period)
                if period == 'today':
                    records_to_process = all_records
                else:
                    records_to_process = all_records[:limit] if limit < len(all_records) else all_records
                
                for record in records_to_process:
                    if 'date' in record and 'close' in record:
                        try:
                            if period == 'today' and 'T' in record['date']:
                                date_str = record['date']
                            else:
                                date_str = record['date'].split('T')[0]
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
        
        return {
            'success': overall_success,
            'data': data,
            'errors': global_errors
        }
    
    def save_to_database(self, symbol: str) -> Dict:
        """Save current stock data to CSV database."""
        symbol = symbol.upper()
        
        self.logger.info(f"Saving stock data to database for {symbol}")
        
        try:
            # Get fresh data
            historical_result = self.fetcher.get_historical_data(symbol, config.api.historical_data_limit)
            
            if not historical_result['success'] or not historical_result['data']:
                raise DataFetchException(f"No data available to save for {symbol}: {historical_result['message']}")
            
            # Save to database
            db_result = save_to_database_csv(historical_result['data'], symbol)
            
            if not db_result['success']:
                raise DatabaseException(f"Failed to save to database: {db_result['message']}")
            
            log_data_operation(self.logger, "save", symbol, db_result['records'])
            
            return {
                'success': db_result['success'],
                'symbol': symbol,
                'message': db_result['message'],
                'records_added': db_result['records'],
                'total_records': db_result['total_records'],
                'updated': db_result['updated'],
                'filename': db_result['filename']
            }
            
        except Exception as e:
            log_error(self.logger, e, f"save_to_database for {symbol}")
            raise
    
    def load_from_database(self, symbol: str) -> Dict:
        """Load stock data from CSV database."""
        symbol = symbol.upper()
        
        # Try to load from database
        db_result = load_from_database_csv(symbol)
        
        if not db_result['success'] or not db_result['data']:
            return {
                'success': False,
                'symbol': symbol,
                'dates': [],
                'prices': [],
                'volumes': [],
                'source': 'database',
                'records': 0,
                'message': db_result['message']
            }
        
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
        
        return {
            'success': True,
            'symbol': symbol,
            'dates': dates,
            'prices': prices,
            'volumes': volumes,
            'source': 'database',
            'records': len(dates),
            'message': f'Loaded from database: {db_result["filename"]}',
            'filename': db_result['filename']
        }
    
    def get_technical_analysis(self, symbol: str, period: str = 'default') -> Dict:
        """Get technical analysis for a specific symbol and period."""
        symbol = symbol.upper()
        
        self.logger.info(f"Getting technical analysis for {symbol} (period: {period})")
        
        try:
            # Get historical data for analysis
            db_load_result = load_from_database_csv(symbol)
            
            if not db_load_result['success'] or not db_load_result['data']:
                return {
                    'success': False,
                    'symbol': symbol,
                    'message': f'No historical data available for {symbol}',
                    'indicators': {},
                    'signals': {
                        'overall_signal': 'HOLD',
                        'confidence': 0,
                        'reasons': ['No data available for analysis']
                    }
                }
            
            # Process database records
            all_records = self._process_database_records(db_load_result['data'])
            records_to_process = self._filter_records_by_period(all_records, period)
            
            if not records_to_process:
                return {
                    'success': False,
                    'symbol': symbol,
                    'message': f'No data available for period: {period}',
                    'indicators': {},
                    'signals': {
                        'overall_signal': 'HOLD',
                        'confidence': 0,
                        'reasons': [f'No data for period: {period}']
                    }
                }
            
            # Perform technical analysis
            analysis_result = self.technical_analysis.get_technical_analysis(symbol, records_to_process)
            
            # Add period information
            analysis_result['period'] = period
            analysis_result['data_points'] = len(records_to_process)
            
            return analysis_result
            
        except Exception as e:
            log_error(self.logger, e, f"get_technical_analysis for {symbol}")
            return {
                'success': False,
                'symbol': symbol,
                'message': f'Technical analysis failed: {str(e)}',
                'indicators': {},
                'signals': {
                    'overall_signal': 'HOLD',
                    'confidence': 0,
                    'reasons': [f'Analysis error: {str(e)}']
                }
            }
    
    def get_signals(self, symbol: str, period: str = 'default') -> Dict:
        """Get trading signals for a specific symbol."""
        symbol = symbol.upper()
        
        self.logger.info(f"Getting trading signals for {symbol} (period: {period})")
        
        try:
            # Get technical analysis
            analysis = self.get_technical_analysis(symbol, period)
            
            if not analysis['success']:
                return analysis
            
            # Extract signals and latest values
            signals = analysis['signals']
            latest_values = analysis['latest_values']
            
            # Format response for signals endpoint
            return {
                'success': True,
                'symbol': symbol,
                'period': period,
                'signal': signals['overall_signal'],
                'confidence': signals['confidence'],
                'reasons': signals['reasons'],
                'latest_indicators': latest_values,
                'analysis_date': analysis['analysis_date'],
                'data_points': analysis['data_points']
            }
            
        except Exception as e:
            log_error(self.logger, e, f"get_signals for {symbol}")
            return {
                'success': False,
                'symbol': symbol,
                'message': f'Signal generation failed: {str(e)}',
                'signal': 'HOLD',
                'confidence': 0,
                'reasons': [f'Error: {str(e)}']
            }
    
    def get_price_prediction(self, symbol: str, days_ahead: int = 30, retrain: bool = False) -> Dict:
        """Get price predictions for a specific symbol."""
        symbol = symbol.upper()
        
        self.logger.info(f"Getting price predictions for {symbol} ({days_ahead} days ahead)")
        
        try:
            # Get historical data for prediction
            db_load_result = load_from_database_csv(symbol)
            
            if not db_load_result['success'] or not db_load_result['data']:
                return {
                    'success': False,
                    'symbol': symbol,
                    'message': f'No historical data available for {symbol}',
                    'predictions': [],
                    'metrics': {}
                }
            
            # Process database records
            all_records = self._process_database_records(db_load_result['data'])
            
            if not all_records:
                return {
                    'success': False,
                    'symbol': symbol,
                    'message': f'No valid data records for {symbol}',
                    'predictions': [],
                    'metrics': {}
                }
            
            # Generate predictions
            result = self.prediction_service.generate_predictions(
                symbol, all_records, days_ahead, retrain
            )
            
            return result
            
        except Exception as e:
            log_error(self.logger, e, f"get_price_prediction for {symbol}")
            return {
                'success': False,
                'symbol': symbol,
                'message': f'Price prediction failed: {str(e)}',
                'predictions': [],
                'metrics': {}
            }
    
    def get_model_performance(self, symbol: str) -> Dict:
        """Get model performance metrics for a symbol."""
        symbol = symbol.upper()
        
        self.logger.info(f"Getting model performance for {symbol}")
        
        try:
            # Try to load existing model to get metrics
            model = self.prediction_service.load_model(symbol)
            
            if model is None:
                return {
                    'success': False,
                    'symbol': symbol,
                    'message': f'No trained model found for {symbol}',
                    'metrics': {}
                }
            
            # For now, return basic model info
            # In a full implementation, you'd store and retrieve actual metrics
            return {
                'success': True,
                'symbol': symbol,
                'model_status': 'Trained',
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'metrics': {
                    'note': 'Model metrics available after training/retraining'
                }
            }
            
        except Exception as e:
            log_error(self.logger, e, f"get_model_performance for {symbol}")
            return {
                'success': False,
                'symbol': symbol,
                'message': f'Failed to get model performance: {str(e)}',
                'metrics': {}
            } 