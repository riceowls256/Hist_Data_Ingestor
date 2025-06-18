#!/usr/bin/env python3
"""
Test script specifically for statistics schema on ES futures.
"""

import os
import sys
from datetime import datetime, timedelta

# Add project root to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.ingestion.api_adapters.databento_adapter import DatabentoAdapter
from src.utils.custom_logger import get_logger

logger = get_logger(__name__)

def test_statistics_schema():
    """Test the statistics schema for ES futures."""
    
    print("📊 Testing Statistics Schema for ES.c.0...")
    print("=" * 50)
    
    config = {
        "api": {
            "key_env_var": "DATABENTO_API_KEY"
        }
    }
    
    try:
        adapter = DatabentoAdapter(config)
        adapter.connect()
        print("✅ Connected to Databento API")
        
        # Test statistics schema - typically has less frequent data
        test_job = {
            "dataset": "GLBX.MDP3",         # CME dataset
            "schema": "statistics",         # Statistics schema
            "symbols": ["ES.c.0"],          # E-mini S&P 500 continuous
            "stype_in": "continuous",       # Continuous contract
            "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "end_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        }
        
        print(f"📊 Testing statistics for: {test_job['symbols']} on {test_job['dataset']}")
        print(f"📅 Date range: {test_job['start_date']} to {test_job['end_date']}")
        print(f"📋 Schema: {test_job['schema']}")
        
        print("\n🔍 Fetching statistics data...")
        data_store = adapter._fetch_data_chunk(
            dataset=test_job["dataset"],
            schema=test_job["schema"],
            symbols=test_job["symbols"],
            stype_in=test_job["stype_in"],
            start_date=test_job["start_date"],
            end_date=test_job["end_date"]
        )
        
        print(f"📊 Data store type: {type(data_store)}")
        
        # Collect and analyze statistics records
        records = []
        stat_types = {}
        
        for record in data_store:
            records.append(record)
            # Track different statistic types
            if hasattr(record, 'stat_type'):
                stat_type = record.stat_type
                if stat_type not in stat_types:
                    stat_types[stat_type] = 0
                stat_types[stat_type] += 1
        
        print(f"✅ Successfully retrieved {len(records)} statistics records")
        
        if records:
            print(f"\n📋 Statistics Record Analysis:")
            
            # Show stat_type distribution
            print(f"📊 Statistic Types Found:")
            for stat_type, count in sorted(stat_types.items()):
                stat_name = get_stat_type_name(stat_type)
                print(f"   {stat_type}: {stat_name} ({count} records)")
            
            # Analyze a few sample records
            print(f"\n📋 Sample Records:")
            for i, record in enumerate(records[:5]):  # Show first 5 records
                print(f"\n   📄 Record {i+1}:")
                print(f"      Record type: {type(record).__name__}")
                
                if hasattr(record, 'ts_event'):
                    timestamp = record.ts_event
                    dt = datetime.fromtimestamp(timestamp / 1e9)
                    print(f"      📅 Timestamp: {dt} (raw: {timestamp})")
                
                if hasattr(record, 'stat_type'):
                    stat_name = get_stat_type_name(record.stat_type)
                    print(f"      📊 Stat Type: {record.stat_type} ({stat_name})")
                
                if hasattr(record, 'price'):
                    if record.price != 9223372036854775807:  # Check for valid price (not max int64)
                        price = record.price / 1e9
                        print(f"      💰 Price: ${price:.2f}")
                    else:
                        print(f"      💰 Price: N/A (empty)")
                
                if hasattr(record, 'quantity'):
                    if record.quantity != 2147483647:  # Check for valid quantity (not max int32)
                        print(f"      📦 Quantity: {record.quantity:,}")
                    else:
                        print(f"      📦 Quantity: N/A (empty)")
                
                if hasattr(record, 'instrument_id'):
                    print(f"      🏷️  Instrument ID: {record.instrument_id}")
                
                # Show all non-private attributes
                print(f"      🔍 All attributes:")
                for attr in dir(record):
                    if not attr.startswith('_') and not callable(getattr(record, attr)):
                        value = getattr(record, attr)
                        print(f"         {attr}: {value}")
        
        adapter.disconnect()
        print(f"\n🎉 Statistics Schema Test COMPLETED!")
        return True
        
    except Exception as e:
        print(f"❌ Statistics Test FAILED: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

def get_stat_type_name(stat_type):
    """Convert stat_type number to human-readable name."""
    stat_type_mapping = {
        1: "Opening Price",
        2: "Indicative Opening Price", 
        3: "Settlement Price",
        4: "Trading Session High Price",
        5: "Trading Session Low Price",
        6: "Trading Session VWAP",
        7: "Clearing Price", 
        8: "Open Interest",
        9: "Open Interest",
        10: "Fixing Price",
        11: "Close Price",
        12: "Net Change",
        13: "VWAP",
        14: "Official Settlement Price",
        15: "Previous Day Settlement Price",
        # Add more mappings as needed
    }
    return stat_type_mapping.get(stat_type, f"Unknown Stat Type {stat_type}")

def test_specific_stat_types():
    """Test specific statistic types we're interested in."""
    
    print("\n🔍 Looking for Specific Statistics Types...")
    print("=" * 50)
    
    config = {
        "api": {
            "key_env_var": "DATABENTO_API_KEY"
        }
    }
    
    adapter = DatabentoAdapter(config)
    adapter.connect()
    
    # Get more data to find settlement prices and open interest
    test_job = {
        "dataset": "GLBX.MDP3",
        "schema": "statistics",
        "symbols": ["ES.c.0"],
        "stype_in": "continuous", 
        "start_date": (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    }
    
    print(f"📊 Extended search: {test_job['start_date']} to {test_job['end_date']}")
    
    data_store = adapter._fetch_data_chunk(
        dataset=test_job["dataset"],
        schema=test_job["schema"],
        symbols=test_job["symbols"],
        stype_in=test_job["stype_in"],
        start_date=test_job["start_date"],
        end_date=test_job["end_date"]
    )
    
    # Look for settlement prices and open interest specifically
    settlement_records = []
    open_interest_records = []
    
    for record in data_store:
        if hasattr(record, 'stat_type'):
            if record.stat_type in [3, 14, 15]:  # Settlement price types
                settlement_records.append(record)
            elif record.stat_type in [8, 9]:  # Open interest types
                open_interest_records.append(record)
    
    print(f"\n📊 Settlement Price Records Found: {len(settlement_records)}")
    for record in settlement_records[:3]:  # Show first 3
        if hasattr(record, 'price') and record.price != 9223372036854775807:
            dt = datetime.fromtimestamp(record.ts_event / 1e9)
            price = record.price / 1e9
            stat_name = get_stat_type_name(record.stat_type)
            print(f"   📅 {dt.date()}: {stat_name} = ${price:.2f}")
    
    print(f"\n📊 Open Interest Records Found: {len(open_interest_records)}")
    for record in open_interest_records[:3]:  # Show first 3
        if hasattr(record, 'quantity') and record.quantity != 2147483647:
            dt = datetime.fromtimestamp(record.ts_event / 1e9)
            stat_name = get_stat_type_name(record.stat_type)
            print(f"   📅 {dt.date()}: {stat_name} = {record.quantity:,} contracts")
    
    adapter.disconnect()
    return len(settlement_records), len(open_interest_records)

if __name__ == "__main__":
    print("📊 Statistics Schema Test Suite")
    print("=" * 40)
    
    # Check environment
    api_key = os.getenv("DATABENTO_API_KEY")
    if not api_key:
        print("❌ DATABENTO_API_KEY not set!")
        sys.exit(1)
    
    print(f"✅ API key found: {api_key[:6]}...")
    
    # Test statistics schema
    success = test_statistics_schema()
    
    if success:
        # Look for specific stat types
        settlement_count, oi_count = test_specific_stat_types()
        print(f"\n✅ Statistics Schema Test COMPLETED!")
        print(f"   Settlement Records: {settlement_count}")
        print(f"   Open Interest Records: {oi_count}")
    else:
        print("\n❌ Statistics schema test failed.")
        sys.exit(1) 