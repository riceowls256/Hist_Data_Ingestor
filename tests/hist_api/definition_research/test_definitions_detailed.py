#!/usr/bin/env python3
"""
Detailed Definition Schema Analysis
Finding ES definitions by examining record structure and using symbology mapping
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

import databento as db
from datetime import datetime

def find_es_definitions():
    """Find ES definitions using symbology mapping and detailed analysis"""
    print("🔍 DETAILED DEFINITION ANALYSIS FOR ES")
    print("="*60)
    
    client = db.Historical()
    print("✅ Connected to Databento API")
    
    # Step 1: Use symbology to find ES instrument IDs
    print("\n📊 Step 1: Finding ES instrument IDs via symbology...")
    print("-" * 50)
    
    try:
        # Get symbology mapping for ES
        symbology = client.symbology.resolve(
            dataset="GLBX.MDP3",
            symbols=["ES.c.0"],
            stype_in="continuous",
            stype_out="instrument_id",
            start_date="2025-01-01"
        )
        
        print("📋 ES Symbology Mapping:")
        for mapping in symbology:
            print(f"   Symbol: {mapping.input_symbol}")
            print(f"   Instrument ID: {mapping.output_symbol}")
            print(f"   Start Date: {mapping.start_date}")
            print(f"   End Date: {mapping.end_date}")
            
            # Now search for definitions with this instrument ID
            es_instrument_id = int(mapping.output_symbol)
            
            print(f"\n🔍 Searching definitions for Instrument ID {es_instrument_id}...")
            
            # Get definitions without symbol filter, then filter by instrument_id
            data = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                schema="definition",
                start="2024-12-01",
                end="2025-01-31",
                limit=10000
            )
            
            es_definitions = []
            total_records = 0
            
            for record in data:
                total_records += 1
                if record.instrument_id == es_instrument_id:
                    es_definitions.append(record)
                    
            print(f"📊 Searched {total_records} definition records")
            print(f"✅ Found {len(es_definitions)} ES definition records!")
            
            # Show ES definition details
            for i, record in enumerate(es_definitions[:3]):  # Show first 3
                print(f"\n📋 ES Definition Record {i+1}:")
                print(f"   Instrument ID: {record.instrument_id}")
                print(f"   Time: {record.pretty_ts_event}")
                print(f"   Record Type: {type(record).__name__}")
                
                # Show all attributes
                attrs = [attr for attr in dir(record) if not attr.startswith('_') and not callable(getattr(record, attr))]
                for attr in attrs:
                    try:
                        value = getattr(record, attr)
                        if not str(value).startswith('<'):  # Skip complex objects
                            print(f"   {attr}: {value}")
                    except:
                        pass
                print()
                
    except Exception as e:
        print(f"❌ Symbology error: {e}")
    
    # Step 2: Alternative approach - examine record structure
    print("\n📊 Step 2: Examining definition record structure...")
    print("-" * 50)
    
    try:
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            schema="definition",
            start="2025-01-01",
            end="2025-01-02",
            limit=10
        )
        
        for i, record in enumerate(data):
            if i >= 3:  # Just show first 3 records
                break
                
            print(f"\n📋 Sample Definition Record {i+1}:")
            print(f"   Type: {type(record).__name__}")
            print(f"   Instrument ID: {record.instrument_id}")
            print(f"   Time: {record.pretty_ts_event}")
            
            # Show complete record structure
            attrs = [attr for attr in dir(record) if not attr.startswith('_') and not callable(getattr(record, attr))]
            for attr in sorted(attrs):
                try:
                    value = getattr(record, attr)
                    if not str(value).startswith('<'):  # Skip complex objects
                        print(f"   {attr}: {value} ({type(value).__name__})")
                except:
                    pass
            print("-" * 30)
            
    except Exception as e:
        print(f"❌ Error examining records: {e}")

if __name__ == "__main__":
    find_es_definitions() 