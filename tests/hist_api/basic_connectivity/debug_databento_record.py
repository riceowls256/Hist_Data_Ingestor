#!/usr/bin/env python3
"""
Debug script to inspect Databento record structure.
"""

import os
import sys
from datetime import datetime, timedelta

# Add project root to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.ingestion.api_adapters.databento_adapter import DatabentoAdapter

def debug_record_structure():
    """Debug the actual structure of databento records."""
    
    config = {
        "api": {
            "key_env_var": "DATABENTO_API_KEY"
        }
    }
    
    adapter = DatabentoAdapter(config)
    adapter.connect()
    
    # Fetch raw data directly
    test_job = {
        "dataset": "XNAS.ITCH",
        "schema": "ohlcv-1d",
        "symbols": ["AAPL"],
        "stype_in": "native",
        "start_date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    }
    
    print("🔍 Fetching raw data to inspect record structure...")
    
    # Get raw data store
    data_store = adapter._fetch_data_chunk(
        dataset=test_job["dataset"],
        schema=test_job["schema"],
        symbols=test_job["symbols"],
        stype_in=test_job["stype_in"],
        start_date=test_job["start_date"],
        end_date=test_job["end_date"]
    )
    
    print(f"📊 Data store type: {type(data_store)}")
    
    # Try to iterate through records
    record_count = 0
    first_record = None
    for record in data_store:
        if first_record is None:
            first_record = record
        record_count += 1
        if record_count >= 1:  # Just get the first record
            break
    
    print(f"📊 Total records found: {record_count}")
    
    if first_record is not None:
        record = first_record
        print(f"\n📋 First record type: {type(record)}")
        print(f"📋 Record attributes: {dir(record)}")
        
        # Check available methods
        methods = [method for method in dir(record) if not method.startswith('_')]
        print(f"📋 Available methods: {methods}")
        
        # Try different conversion methods
        print(f"\n🔧 Testing conversion methods:")
        
        if hasattr(record, 'model_dump'):
            try:
                data = record.model_dump()
                print(f"✅ model_dump() works: {list(data.keys())}")
            except Exception as e:
                print(f"❌ model_dump() failed: {e}")
        
        if hasattr(record, 'as_dict'):
            try:
                data = record.as_dict()
                print(f"✅ as_dict() works: {list(data.keys())}")
            except Exception as e:
                print(f"❌ as_dict() failed: {e}")
                
        if hasattr(record, 'to_dict'):
            try:
                data = record.to_dict()
                print(f"✅ to_dict() works: {list(data.keys())}")
            except Exception as e:
                print(f"❌ to_dict() failed: {e}")
        
        # Try direct attribute access
        print(f"\n🔧 Trying direct attribute access:")
        common_fields = ['ts_event', 'open', 'high', 'low', 'close', 'volume']
        for field in common_fields:
            if hasattr(record, field):
                value = getattr(record, field)
                print(f"✅ {field}: {value} (type: {type(value)})")
        
        # Try to convert manually using all attributes
        print(f"\n🔧 Manual conversion attempt:")
        try:
            manual_dict = {}
            for attr in dir(record):
                if not attr.startswith('_') and not callable(getattr(record, attr)):
                    manual_dict[attr] = getattr(record, attr)
            print(f"✅ Manual dict keys: {list(manual_dict.keys())}")
        except Exception as e:
            print(f"❌ Manual conversion failed: {e}")
    
    adapter.disconnect()

if __name__ == "__main__":
    debug_record_structure() 