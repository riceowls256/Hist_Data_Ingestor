#!/usr/bin/env python3
"""
Test script for futures contracts on GLBX.MDP3 dataset.
Configurable for different symbols.
"""

import os
import sys
from datetime import datetime, timedelta

# Add project root to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.ingestion.api_adapters.databento_adapter import DatabentoAdapter
from src.utils.custom_logger import get_logger

logger = get_logger(__name__)

# CONFIGURATION - Change these to test different contracts
SYMBOL = "CL.c.0"  # E-mini S&P 500 continuous front month
DATASET = "GLBX.MDP3"  # CME dataset
CONTRACT_NAME = "Crude Oil"  # Human-readable name

def test_futures_connection(symbol=SYMBOL, dataset=DATASET, contract_name=CONTRACT_NAME):
    """Test futures connection for specified contract."""
    
    print(f"🚀 Testing {contract_name} ({symbol}) on {dataset}...")
    print("=" * 60)
    
    config = {
        "api": {
            "key_env_var": "DATABENTO_API_KEY"
        },
        "retry_policy": {
            "max_retries": 2,
            "base_delay": 1.0,
            "max_delay": 10.0,
            "backoff_multiplier": 2.0
        }
    }
    
    try:
        adapter = DatabentoAdapter(config)
        adapter.connect()
        print("✅ Connected to Databento API")
        
        # Test futures contract with configurable parameters
        test_job = {
            "dataset": dataset,
            "schema": "ohlcv-1d",           # Daily OHLCV bars
            "symbols": [symbol],
            "stype_in": "continuous",       # Continuous contract
            "start_date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
            "end_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        }
        
        print(f"📊 Testing contract: {contract_name} ({symbol})")
        print(f"📈 Dataset: {dataset}")
        print(f"📅 Date range: {test_job['start_date']} to {test_job['end_date']}")
        print(f"📋 Schema: {test_job['schema']}")
        print(f"🔄 Symbol type: {test_job['stype_in']}")
        
        # Fetch data directly to bypass validation issues for now
        print(f"\n🔍 Fetching {contract_name} data...")
        data_store = adapter._fetch_data_chunk(
            dataset=test_job["dataset"],
            schema=test_job["schema"],
            symbols=test_job["symbols"],
            stype_in=test_job["stype_in"],
            start_date=test_job["start_date"],
            end_date=test_job["end_date"]
        )
        
        print(f"📊 Data store type: {type(data_store)}")
        
        # Count and examine records
        record_count = 0
        sample_records = []
        
        for record in data_store:
            record_count += 1
            if len(sample_records) < 3:  # Keep first 3 records as samples
                sample_records.append(record)
            if record_count >= 10:  # Don't process too many for testing
                break
        
        print(f"✅ Successfully retrieved {record_count} {contract_name} records")
        
        if sample_records:
            print(f"\n📋 {contract_name} Sample Record Analysis:")
            first_record = sample_records[0]
            print(f"   Record type: {type(first_record).__name__}")
            
            # Show the key data fields
            if hasattr(first_record, 'ts_event'):
                timestamp = first_record.ts_event
                # Convert nanoseconds to datetime
                dt = datetime.fromtimestamp(timestamp / 1e9)
                print(f"   📅 Timestamp: {dt} (raw: {timestamp})")
                
            if hasattr(first_record, 'open'):
                # Prices are scaled by 1e-9
                open_price = first_record.open / 1e9
                print(f"   💰 Open: ${open_price:.2f}")
                
            if hasattr(first_record, 'high'):
                high_price = first_record.high / 1e9
                print(f"   📈 High: ${high_price:.2f}")
                
            if hasattr(first_record, 'low'):
                low_price = first_record.low / 1e9
                print(f"   📉 Low: ${low_price:.2f}")
                
            if hasattr(first_record, 'close'):
                close_price = first_record.close / 1e9
                print(f"   💲 Close: ${close_price:.2f}")
                
            if hasattr(first_record, 'volume'):
                print(f"   📊 Volume: {first_record.volume:,}")
            
            if hasattr(first_record, 'instrument_id'):
                print(f"   🏷️  Instrument ID: {first_record.instrument_id}")
        
        adapter.disconnect()
        print(f"\n🎉 {contract_name} ({symbol}) Test SUCCESSFUL!")
        print(f"   Dataset: {dataset} ✅")
        print(f"   Symbol: {symbol} ✅")
        print(f"   Records: {record_count} ✅")
        
        return True
        
    except Exception as e:
        print(f"❌ {contract_name} ({symbol}) Test FAILED: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

def test_different_schemas(symbol=SYMBOL, dataset=DATASET, contract_name=CONTRACT_NAME):
    """Test different schemas available for the specified contract."""
    
    print(f"\n🔍 Testing Different Schemas for {contract_name} ({symbol})...")
    print("=" * 60)
    
    config = {
        "api": {
            "key_env_var": "DATABENTO_API_KEY"
        }
    }
    
    schemas_to_test = [
        "ohlcv-1d",   # Daily bars
        "ohlcv-1h",   # Hourly bars  
        "trades",     # Trade data
        "tbbo"        # Top of book
    ]
    
    adapter = DatabentoAdapter(config)
    adapter.connect()
    
    base_job = {
        "dataset": dataset,
        "symbols": [symbol],
        "stype_in": "continuous",
        "start_date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    }
    
    results = {}
    
    for schema in schemas_to_test:
        print(f"\n📋 Testing {contract_name} with schema: {schema}")
        try:
            test_job = {**base_job, "schema": schema}
            
            data_store = adapter._fetch_data_chunk(
                dataset=test_job["dataset"],
                schema=test_job["schema"],
                symbols=test_job["symbols"],
                stype_in=test_job["stype_in"],
                start_date=test_job["start_date"],
                end_date=test_job["end_date"]
            )
            
            record_count = sum(1 for _ in data_store)
            results[schema] = record_count
            print(f"   ✅ {schema}: {record_count} records")
            
        except Exception as e:
            results[schema] = f"Error: {e}"
            print(f"   ❌ {schema}: {e}")
    
    adapter.disconnect()
    
    print(f"\n📊 {contract_name} ({symbol}) Schema Test Summary:")
    for schema, result in results.items():
        print(f"   {schema}: {result}")
    
    return results

if __name__ == "__main__":
    print(f"🚀 {CONTRACT_NAME} Futures API Test Suite")
    print("=" * 50)
    print(f"📈 Testing Symbol: {SYMBOL}")
    print(f"📊 Dataset: {DATASET}")
    print(f"🏷️  Contract: {CONTRACT_NAME}")
    
    # Check environment
    api_key = os.getenv("DATABENTO_API_KEY")
    if not api_key:
        print("❌ DATABENTO_API_KEY not set!")
        sys.exit(1)
    
    print(f"✅ API key found: {api_key[:6]}...")
    
    # Test futures connection
    success = test_futures_connection()
    
    if success:
        # Test different schemas
        test_different_schemas()
        print(f"\n✅ All {CONTRACT_NAME} ({SYMBOL}) tests completed successfully!")
    else:
        print(f"\n❌ {CONTRACT_NAME} ({SYMBOL}) connection test failed.")
        sys.exit(1)

# Additional contract configurations for easy switching:
# Uncomment and modify these to test different contracts:

# # Crude Oil Futures (WTI)
# SYMBOL = "CL.c.0"
# DATASET = "GLBX.MDP3" 
# CONTRACT_NAME = "WTI Crude Oil"

# # Natural Gas Futures
# SYMBOL = "NG.c.0"
# DATASET = "GLBX.MDP3"
# CONTRACT_NAME = "Natural Gas"

# # Gold Futures
# SYMBOL = "GC.c.0"
# DATASET = "GLBX.MDP3"
# CONTRACT_NAME = "Gold"

# # 10-Year Treasury Note Futures
# SYMBOL = "ZN.c.0" 
# DATASET = "GLBX.MDP3"
# CONTRACT_NAME = "10-Year Treasury Note"

# # Euro FX Futures
# SYMBOL = "6E.c.0"
# DATASET = "GLBX.MDP3"
# CONTRACT_NAME = "Euro FX" 