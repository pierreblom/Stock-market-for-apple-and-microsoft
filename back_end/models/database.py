"""
Database operations for CSV-based stock data storage.
"""

import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from ..config import config

# Type definitions
StockRecord = Dict[str, Union[str, float, int]]
DatabaseResult = Dict[str, Union[bool, str, int, List[StockRecord], None]]
TrackingSummary = Dict[str, Union[str, float, int]]


def save_to_database_csv(
    data: List[StockRecord], 
    symbol: str, 
    update_existing: bool = True
) -> Optional[DatabaseResult]:
    """
    Save/update stock data to persistent CSV database files.
    
    Args:
        data: List of stock records to save
        symbol: Stock symbol for the database file
        update_existing: Whether to update existing database or create new
        
    Returns:
        Dictionary containing operation result, or None if no data provided
    """
    try:
        if not data or len(data) == 0:
            return None
            
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Create persistent database filename (no timestamps!)
        filename = f"{symbol}_database.csv"
        filepath = config.export_dir / filename
        
        if filepath.exists() and update_existing:
            try:
                # Read existing database
                existing_df = pd.read_csv(filepath)
                
                # Merge data (update existing dates, add new dates)
                # Create a copy to avoid modifying original data
                df_copy = df.copy()
                existing_df_copy = existing_df.copy()
                
                # Ensure date columns are strings for comparison
                df_copy['date'] = df_copy['date'].astype(str)
                existing_df_copy['date'] = existing_df_copy['date'].astype(str)
                
                # Remove any existing dates from the old data to avoid duplicates
                existing_dates = set(df_copy['date'])
                filtered_existing = existing_df_copy[~existing_df_copy['date'].isin(existing_dates)]
                
                # Combine old (non-overlapping) + new data
                combined_df = pd.concat([filtered_existing, df_copy], ignore_index=True)
                
                # Sort by date
                combined_df = combined_df.sort_values('date')
                
                # Check if data actually changed
                if len(combined_df) == len(existing_df) and existing_df.equals(combined_df):
                    return {
                        'success': True,
                        'filename': filename,
                        'filepath': str(filepath),
                        'records': len(df),
                        'total_records': len(combined_df),
                        'message': f'No changes needed - database up to date ({len(combined_df)} total records)',
                        'updated': False
                    }
                
                # Save updated database
                combined_df.to_csv(filepath, index=False)
                
                return {
                    'success': True,
                    'filename': filename,
                    'filepath': str(filepath),
                    'records': len(df),
                    'total_records': len(combined_df),
                    'message': f'Database updated: +{len(df)} new records, {len(combined_df)} total',
                    'updated': True
                }
                
            except Exception as e:
                logging.warning(f"Error updating existing database {filename}: {e}")
                # If update fails, create new file
                df.to_csv(filepath, index=False)
                return {
                    'success': True,
                    'filename': filename,
                    'filepath': str(filepath),
                    'records': len(df),
                    'total_records': len(df),
                    'message': f'Created new database: {len(df)} records',
                    'updated': True
                }
        else:
            # Create new database file
            df.to_csv(filepath, index=False)
            return {
                'success': True,
                'filename': filename,
                'filepath': str(filepath),
                'records': len(df),
                'total_records': len(df),
                'message': f'Created new database: {len(df)} records',
                'updated': True
            }
        
    except Exception as e:
        return {
            'success': False,
            'filename': None,
            'filepath': None,
            'records': 0,
            'total_records': 0,
            'message': f'Database error: {str(e)}',
            'updated': False
        }


def load_from_database_csv(symbol: str) -> DatabaseResult:
    """
    Load stock data from persistent CSV database.
    
    Args:
        symbol: Stock symbol to load data for
        
    Returns:
        Dictionary containing operation result and data
    """
    try:
        filename = f"{symbol}_database.csv"
        filepath = config.export_dir / filename
        
        if not filepath.exists():
            return {
                'success': False,
                'data': [],
                'message': f'No database file found for {symbol}',
                'records': 0
            }
        
        df = pd.read_csv(filepath)
        
        # Convert to records format
        records: List[StockRecord] = df.to_dict('records')
        
        return {
            'success': True,
            'data': records,
            'message': f'Loaded {len(records)} records from database',
            'records': len(records),
            'filename': filename
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': [],
            'message': f'Error loading database: {str(e)}',
            'records': 0
        } 


def update_database_from_tracking() -> DatabaseResult:
    """
    Summarize intra-day tracking data into daily OHLCV records and
    update the persistent database files.
    
    Returns:
        Dictionary containing operation result and updated symbols
    """
    try:
        # Read the consolidated tracking file
        tracking_filename = "price_tracking.csv"
        tracking_filepath = config.export_dir / tracking_filename
        
        if not tracking_filepath.exists():
            return {
                'success': False,
                'message': 'No tracking file found to process.',
                'updated_symbols': []
            }
        
        df = pd.read_csv(tracking_filepath)
        
        if df.empty:
            return {
                'success': True,
                'message': 'Tracking file is empty, no updates made.',
                'updated_symbols': []
            }

        # Convert timestamp to datetime objects for sorting
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values(['symbol', 'timestamp'])

        # Group by symbol and date
        grouped = df.groupby(['symbol', pd.Grouper(key='timestamp', freq='D')])
        
        all_summaries: List[Tuple[str, TrackingSummary]] = []
        for (symbol, date), group in grouped:
            if not group.empty:
                summary: TrackingSummary = {
                    'date': date.strftime('%Y-%m-%d'),
                    'open': group['price'].iloc[0],
                    'high': group['price'].max(),
                    'low': group['price'].min(),
                    'close': group['price'].iloc[-1],
                    'volume': 0  # Volume is not tracked in real-time data
                }
                all_summaries.append((symbol, summary))

        if not all_summaries:
            return {
                'success': True,
                'message': 'No daily data to summarize from tracking file.',
                'updated_symbols': []
            }

        # Update database for each symbol
        updated_symbols: Dict[str, Dict[str, Any]] = {}
        symbols_to_update = set(s for s, _ in all_summaries)

        for symbol in symbols_to_update:
            symbol_summaries = [s for sym, s in all_summaries if sym == symbol]
            result = save_to_database_csv(symbol_summaries, symbol)
            updated_symbols[symbol] = result

        return {
            'success': True,
            'message': f'Successfully processed tracking data for {len(symbols_to_update)} symbols.',
            'updated_symbols': updated_symbols
        }

    except Exception as e:
        logging.error(f"Error updating database from tracking file: {e}")
        return {
            'success': False,
            'message': f'An error occurred: {str(e)}',
            'updated_symbols': []
        } 