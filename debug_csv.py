#!/usr/bin/env python3
"""
Debug script to test CSV reading functionality.
"""

import sys
import os
sys.path.append('back_end')

from back_end.models.database import load_from_database_csv
from back_end.config import config

def test_csv_reading():
    print("Testing CSV reading...")
    
    # Test the load function
    result = load_from_database_csv('NVDA')
    
    print(f"Success: {result['success']}")
    print(f"Records loaded: {result['records']}")
    print(f"Message: {result['message']}")
    
    if result['success'] and result['data']:
        print(f"First record: {result['data'][0]}")
        print(f"Last record: {result['data'][-1]}")
        print(f"Total records in data: {len(result['data'])}")
        
        # Check for any records with missing date
        missing_date = [r for r in result['data'] if 'date' not in r]
        print(f"Records missing 'date' field: {len(missing_date)}")
        
        if missing_date:
            print(f"Example record without date: {missing_date[0]}")
    
    # Check file directly
    import pandas as pd
    filepath = config.export_dir / "NVDA_database.csv"
    print(f"\nDirect pandas read of {filepath}:")
    
    if filepath.exists():
        df = pd.read_csv(filepath)
        print(f"Pandas rows: {len(df)}")
        print(f"Pandas columns: {list(df.columns)}")
        print(f"First 3 rows:")
        print(df.head(3))
    else:
        print(f"File does not exist: {filepath}")

if __name__ == "__main__":
    test_csv_reading() 