"""
Database service for handling CSV database operations.
"""

import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from ..config import EXPORT_DIR, AUTO_DOWNLOAD_SYMBOLS
from ..models.data_fetcher import MarketDataFetcher
from ..models.database import save_to_database_csv, load_from_database_csv, update_database_from_tracking
from ..utils.exceptions import DatabaseException, FileNotFoundException
from ..utils.helpers import cleanup_duplicate_csv_files


class DatabaseService:
    """Service for database operations."""
    
    def __init__(self):
        self.fetcher = MarketDataFetcher()
    
    def list_csv_files(self) -> Dict:
        """List all available CSV files."""
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
        
        return {
            'success': True,
            'files': csv_files,
            'count': len(csv_files)
        }
    
    def list_database_files(self) -> Dict:
        """List all available CSV database files."""
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
        
        return {
            'success': True,
            'databases': files_info,
            'total_files': len(files_info),
            'message': f'Found {len(files_info)} database files'
        }
    
    def update_all_databases(self) -> Dict:
        """Update all database files with fresh data."""
        symbols = ['NVDA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']  # Add more as needed
        results = {}
        
        for symbol in symbols:
            try:
                # Get fresh data
                historical_result = self.fetcher.get_historical_data(symbol, 60)
                
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
        
        return {
            'success': True,
            'results': results,
            'summary': {
                'successful_symbols': successful,
                'total_symbols': len(symbols),
                'total_records': total_records
            },
            'message': f'Updated {successful}/{len(symbols)} databases with {total_records} total records'
        }
    
    def update_from_tracking(self) -> Dict:
        """Update database files from the real-time tracking file."""
        result = update_database_from_tracking()
        return result
    
    def cleanup_duplicates(self) -> Dict:
        """Clean up duplicate CSV files."""
        result = cleanup_duplicate_csv_files()
        return {
            'success': True,
            'message': f"Cleanup complete: Deleted {result['deleted']} duplicates, kept {result['kept']} files",
            'deleted': result['deleted'],
            'kept': result['kept']
        }
    
    def export_stock_data_csv(self, symbol: str, period: str = 'all', month_filter: str = None) -> Dict:
        """Export stock data to CSV format."""
        symbol = symbol.upper()
        
        # Get historical data
        limit = None
        if period != 'all':
            from ..models.data_generator import calculate_data_limit
            limit = calculate_data_limit(period)
        
        historical_result = self.fetcher.get_historical_data(symbol, limit)
        
        if not historical_result['success'] or not historical_result['data']:
            raise DatabaseException(f"No data available for {symbol}: {historical_result['message']}")
        
        # Process data
        all_records = list(reversed(historical_result['data']))
        
        # Apply month filtering if specified
        if month_filter:
            from ..models.data_generator import filter_data_by_month
            all_records = filter_data_by_month(all_records, month_filter)
        
        # Apply client-side filtering based on limit
        records_to_export = all_records[:limit] if limit and limit < len(all_records) else all_records
        
        if not records_to_export:
            raise DatabaseException("No data available for the specified period")
        
        # Save to CSV
        csv_result = save_to_database_csv(records_to_export, symbol)
        
        if not csv_result or not csv_result['success']:
            raise DatabaseException("Failed to create CSV file")
        
        return {
            'success': True,
            'filepath': csv_result['filepath'],
            'filename': csv_result['filename'],
            'records': len(records_to_export),
            'message': f"Successfully exported {len(records_to_export)} records for {symbol}"
        }
    
    def get_file_path(self, filename: str) -> Path:
        """Get file path for a given filename with security checks."""
        # Security check: ensure filename doesn't contain path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            raise FileNotFoundException("Invalid filename")
        
        filepath = EXPORT_DIR / filename
        
        if not filepath.exists():
            raise FileNotFoundException("File not found")
        
        return filepath 