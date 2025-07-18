#!/usr/bin/env python3
"""
Debug script to test the data processing pipeline.
"""

import sys
import os
sys.path.append('back_end')

from back_end.models.database import load_from_database_csv
from back_end.services.stock_service import StockService
from datetime import datetime

def test_processing_pipeline():
    print("Testing data processing pipeline...")
    
    # Load data
    result = load_from_database_csv('NVDA')
    print(f"Initial records loaded: {len(result['data'])}")
    
    if not result['success']:
        print("Failed to load data")
        return
    
    # Test the processing function
    service = StockService()
    
    # Test _process_database_records
    processed_records = service._process_database_records(result['data'])
    print(f"Records after processing: {len(processed_records)}")
    
    if len(processed_records) != len(result['data']):
        print(f"WARNING: Lost {len(result['data']) - len(processed_records)} records during processing!")
        
        # Check what records were lost
        original_dates = set(r['date'] for r in result['data'])
        processed_dates = set(r['date'] for r in processed_records)
        lost_dates = original_dates - processed_dates
        
        if lost_dates:
            print(f"Lost dates (first 5): {list(lost_dates)[:5]}")
    
    # Test filtering for different periods
    periods = ['default', 'week', 'month', 'all']
    
    for period in periods:
        filtered_records = service._filter_records_by_period(processed_records, period)
        print(f"Records for period '{period}': {len(filtered_records)}")
        
        if filtered_records:
            print(f"  Date range: {filtered_records[0]['date']} to {filtered_records[-1]['date']}")
    
    # Test the full get_stock_data function
    print("\nTesting full get_stock_data function:")
    for period in ['default', 'week', 'month', 'all']:
        try:
            stock_data = service.get_stock_data('NVDA', period)
            print(f"Period '{period}': {len(stock_data.get('dates', []))} dates, {len(stock_data.get('prices', []))} prices")
            print(f"  Success: {stock_data.get('success')}")
            print(f"  Current: {stock_data.get('current') is not None}")
        except Exception as e:
            print(f"Period '{period}': Error - {e}")

if __name__ == "__main__":
    test_processing_pipeline() 