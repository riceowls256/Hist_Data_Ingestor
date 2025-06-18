#!/usr/bin/env python3
"""
Comprehensive Definition Schema Investigation
Testing different approaches to get definition data from Databento
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

import databento as db
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_definitions_broad_query():
    """Test definition schema with broader queries"""
    print("🔍 BROAD DEFINITION SCHEMA INVESTIGATION")
    print("="*60)
    
    try:
        client = db.Historical()
        print("✅ Connected to Databento API")
        
        # Test 1: Query ALL symbols (no symbol filter)
        print("\n📊 Test 1: Querying ALL definitions (no symbol filter)")
        print("-" * 50)
        
        try:
            data = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                schema="definition",
                start="2025-01-01",
                end="2025-01-02",
                # No symbols parameter - get all definitions
            )
            
            record_count = 0
            for record in data:
                record_count += 1
                if record_count <= 3:  # Show first 3 records
                    print(f"📋 Definition Record {record_count}:")
                    print(f"   Instrument ID: {record.instrument_id}")
                    print(f"   Time: {record.pretty_ts_event}")
                    if hasattr(record, 'symbol'):
                        print(f"   Symbol: {record.symbol}")
                    print()
                    
            print(f"✅ Found {record_count} definition records (all symbols)")
            
        except Exception as e:
            print(f"❌ Error with broad query: {e}")
        
        # Test 2: Try specific contract months instead of continuous
        print("\n📊 Test 2: Specific contract months")
        print("-" * 50)
        
        contract_symbols = [
            "ESH5",  # March 2025
            "ESM5",  # June 2025
            "ESU5",  # September 2025
            "ESZ5",  # December 2025
        ]
        
        for symbol in contract_symbols:
            try:
                data = client.timeseries.get_range(
                    dataset="GLBX.MDP3",
                    schema="definition",
                    start="2025-01-01",
                    end="2025-01-02",
                    symbols=[symbol]
                )
                
                count = sum(1 for _ in data)
                print(f"   {symbol}: {count} definition records")
                
            except Exception as e:
                print(f"   {symbol}: Error - {e}")
        
        # Test 3: Much longer historical period
        print("\n📊 Test 3: Extended historical period (6 months)")
        print("-" * 50)
        
        try:
            data = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                schema="definition",
                start="2024-06-01",
                end="2024-12-31",
                symbols=["ES.c.0"]
            )
            
            record_count = 0
            for record in data:
                record_count += 1
                if record_count <= 5:  # Show first 5 records
                    print(f"📋 Historical Definition Record {record_count}:")
                    print(f"   Instrument ID: {record.instrument_id}")
                    print(f"   Time: {record.pretty_ts_event}")
                    if hasattr(record, 'symbol'):
                        print(f"   Symbol: {record.symbol}")
                    print()
                    
            print(f"✅ Found {record_count} historical definition records")
            
        except Exception as e:
            print(f"❌ Error with historical query: {e}")
            
        # Test 4: Try different datasets
        print("\n📊 Test 4: Testing other datasets")
        print("-" * 50)
        
        datasets_to_test = [
            "XNAS.ITCH",  # NASDAQ
            "OPRA.PILLAR", # Options
            "DBEQ.BASIC",  # Databento Equity Basic
        ]
        
        for dataset in datasets_to_test:
            try:
                data = client.timeseries.get_range(
                    dataset=dataset,
                    schema="definition",
                    start="2025-01-01",
                    end="2025-01-02",
                    limit=10
                )
                
                count = sum(1 for _ in data)
                print(f"   {dataset}: {count} definition records")
                
            except Exception as e:
                print(f"   {dataset}: Error - {e}")
        
        print("\n🎯 INVESTIGATION COMPLETE!")
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    test_definitions_broad_query() 