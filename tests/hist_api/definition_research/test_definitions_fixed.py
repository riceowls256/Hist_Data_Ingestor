#!/usr/bin/env python3
"""
Fixed Definition Schema Analysis
Properly finding ES definitions using correct symbology mapping
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

import databento as db
from datetime import datetime

def analyze_definitions_correctly():
    """Correctly analyze definition records and find ES data"""
    print("🔍 FIXED DEFINITION ANALYSIS FOR ES")
    print("="*60)
    
    client = db.Historical()
    print("✅ Connected to Databento API")
    
    # Step 1: Check symbology mapping correctly
    print("\n📊 Step 1: Correct symbology mapping...")
    print("-" * 50)
    
    try:
        # Get symbology mapping for ES
        mapping_result = client.symbology.resolve(
            dataset="GLBX.MDP3",
            symbols=["ES.c.0"],
            stype_in="continuous",
            stype_out="instrument_id",
            start_date="2025-01-01"
        )
        
        print("📋 ES Symbology Result:")
        print(f"   Type: {type(mapping_result)}")
        print(f"   Result: {mapping_result}")
        
        # Parse the result correctly
        if hasattr(mapping_result, '__iter__'):
            for i, item in enumerate(mapping_result):
                print(f"   Item {i}: {item} (type: {type(item)})")
                if hasattr(item, '__dict__'):
                    for attr, value in item.__dict__.items():
                        print(f"     {attr}: {value}")
        
    except Exception as e:
        print(f"❌ Symbology error: {e}")
    
    # Step 2: Direct search using known instrument ID from status
    print("\n📊 Step 2: Direct search using known ES instrument ID (4916)...")
    print("-" * 50)
    
    try:
        # We know from status schema that ES instrument ID is 4916
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            schema="definition",
            start="2024-12-01",
            end="2025-01-31",
        )
        
        es_definitions = []
        total_records = 0
        all_instrument_ids = set()
        
        print("🔍 Scanning definition records for ES (instrument ID 4916)...")
        
        for record in data:
            total_records += 1
            all_instrument_ids.add(record.instrument_id)
            
            if record.instrument_id == 4916:  # ES instrument ID from status schema
                es_definitions.append(record)
                
            # Show progress every 10000 records
            if total_records % 10000 == 0:
                print(f"   Scanned {total_records} records...")
                
        print(f"\n📊 SCAN RESULTS:")
        print(f"   Total records scanned: {total_records}")
        print(f"   Unique instrument IDs: {len(all_instrument_ids)}")
        print(f"   ES definitions found: {len(es_definitions)}")
        
        if es_definitions:
            print(f"\n✅ FOUND ES DEFINITION RECORDS!")
            for i, record in enumerate(es_definitions[:3]):
                print(f"\n📋 ES Definition {i+1}:")
                print(f"   Instrument ID: {record.instrument_id}")
                print(f"   Time: {record.pretty_ts_event}")
                print(f"   Record Type: {type(record).__name__}")
                
                # Show all non-complex attributes
                attrs = [attr for attr in dir(record) if not attr.startswith('_') and not callable(getattr(record, attr))]
                for attr in sorted(attrs):
                    try:
                        value = getattr(record, attr)
                        if not str(value).startswith('<') and attr not in ['hd']:
                            print(f"   {attr}: {value}")
                    except:
                        pass
        else:
            print(f"❌ No ES definitions found with instrument ID 4916")
            print(f"📊 Sample instrument IDs found: {sorted(list(all_instrument_ids))[:20]}")
            
    except Exception as e:
        print(f"❌ Error in direct search: {e}")
    
    # Step 3: Show sample definition record structure
    print("\n📊 Step 3: Sample definition record structure...")
    print("-" * 50)
    
    try:
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            schema="definition",
            start="2025-01-01",
            end="2025-01-02",
            limit=5
        )
        
        for i, record in enumerate(data):
            print(f"\n📋 Sample Record {i+1}:")
            print(f"   Type: {type(record).__name__}")
            print(f"   Instrument ID: {record.instrument_id}")
            print(f"   Time: {record.pretty_ts_event}")
            
            # Show key attributes
            key_attrs = ['action', 'currency', 'exchange', 'instrument_class', 'pretty_symbol', 'raw_symbol', 'strike_price', 'underlying']
            for attr in key_attrs:
                if hasattr(record, attr):
                    try:
                        value = getattr(record, attr)
                        print(f"   {attr}: {value}")
                    except:
                        pass
            print("-" * 20)
            
    except Exception as e:
        print(f"❌ Error showing samples: {e}")

if __name__ == "__main__":
    analyze_definitions_correctly() 