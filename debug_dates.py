#!/usr/bin/env python3
"""
Debug script to test the date processing issue.
"""

import sys
import os
sys.path.append('back_end')

from back_end.models.database import load_from_database_csv
from back_end.services.stock_service import StockService
from datetime import datetime

def test_date_processing():
    print("Testing date processing...")
    
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
    
    # Check for records without date_obj
    records_without_date_obj = [r for r in processed_records if 'date_obj' not in r]
    print(f"Records without date_obj: {len(records_without_date_obj)}")
    
    if records_without_date_obj:
        print(f"Example record without date_obj: {records_without_date_obj[0]}")
    
    # Check for records with date_obj
    records_with_date_obj = [r for r in processed_records if 'date_obj' in r]
    print(f"Records with date_obj: {len(records_with_date_obj)}")
    
    if records_with_date_obj:
        print(f"Example record with date_obj: {records_with_date_obj[0]}")
        print(f"Date_obj type: {type(records_with_date_obj[0]['date_obj'])}")
    
    # Test filtering for default period
    filtered_records = service._filter_records_by_period(processed_records, 'default')
    print(f"Records after filtering (default): {len(filtered_records)}")
    
    # Test date extraction
    try:
        dates = [r['date_obj'].strftime('%Y-%m-%d') for r in filtered_records]
        print(f"Dates extracted: {len(dates)}")
        print(f"First 3 dates: {dates[:3]}")
    except Exception as e:
        print(f"Error extracting dates: {e}")
        
        # Check what's in the records
        for i, r in enumerate(filtered_records[:3]):
            print(f"Record {i}: {r}")
            if 'date_obj' in r:
                print(f"  date_obj: {r['date_obj']} (type: {type(r['date_obj'])})")

if __name__ == "__main__":
    test_date_processing() 