#!/usr/bin/env python3
"""
Quick test script for the status schema.
Since status schema showed 33 records, let's explore what it contains.
"""

import os
import sys
from datetime import datetime, timedelta

# Add project root to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.ingestion.api_adapters.databento_adapter import DatabentoAdapter
from src.utils.custom_logger import get_logger

logger = get_logger(__name__)

def test_status_schema():
    """Test status schema to see what type of data it contains."""
    
    print("🔍 TESTING STATUS SCHEMA")
    print("=" * 40)
    
    config = {
        "api": {
            "key_env_var": "DATABENTO_API_KEY"
        }
    }
    
    adapter = DatabentoAdapter(config)
    adapter.connect()
    
    test_job = {
        "dataset": "GLBX.MDP3",
        "schema": "status",
        "symbols": ["ES.c.0"],
        "stype_in": "continuous",
        "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    }
    
    print(f"📊 Fetching status data for ES.c.0...")
    data_store = adapter._fetch_data_chunk(
        dataset=test_job["dataset"],
        schema=test_job["schema"],
        symbols=test_job["symbols"],
        stype_in=test_job["stype_in"],
        start_date=test_job["start_date"],
        end_date=test_job["end_date"]
    )
    
    records = []
    for record in data_store:
        records.append(record)
        if len(records) >= 10:  # Get first 10
            break
    
    print(f"✅ Retrieved {len(records)} status records")
    
    if records:
        print(f"\n📊 STATUS RECORD ANALYSIS:")
        print("-" * 30)
        
        first_record = records[0]
        print(f"Record type: {type(first_record).__name__}")
        
        # Show all available fields
        for attr in dir(first_record):
            if not attr.startswith('_') and not callable(getattr(first_record, attr)):
                value = getattr(first_record, attr)
                print(f"  {attr}: {value} ({type(value).__name__})")
        
        # Show multiple records to see variations
        print(f"\n📊 COMPARING STATUS RECORDS:")
        print("-" * 30)
        for i, record in enumerate(records[:3], 1):
            print(f"\nRecord {i}:")
            if hasattr(record, 'ts_event'):
                timestamp = datetime.fromtimestamp(record.ts_event / 1e9)
                print(f"  Time: {timestamp}")
            # Add other key fields as discovered
    
    adapter.disconnect()

if __name__ == "__main__":
    test_status_schema() 