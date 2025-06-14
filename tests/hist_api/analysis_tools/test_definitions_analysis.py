#!/usr/bin/env python3
"""
Definition Records Analysis
Analyzing the 681K definition records found in GLBX.MDP3
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

import databento as db
from collections import defaultdict
import json

def analyze_definition_records():
    """Analyze the definition records we found"""
    print("🔍 ANALYZING DEFINITION RECORDS")
    print("="*50)
    
    client = db.Historical()
    print("✅ Connected to Databento API")
    
    print("\n📊 Fetching definition data for analysis...")
    data = client.timeseries.get_range(
        dataset="GLBX.MDP3",
        schema="definition",
        start="2025-01-01",
        end="2025-01-02",
        limit=50  # Get first 50 records for analysis
    )
    
    print("\n🔍 DETAILED RECORD ANALYSIS:")
    print("-" * 40)
    
    instruments = set()
    record_types = defaultdict(int)
    
    for i, record in enumerate(data):
        instruments.add(record.instrument_id)
        record_types[type(record).__name__] += 1
        
        if i < 10:  # Show first 10 records in detail
            print(f"\n📋 Record {i+1}:")
            print(f"   Type: {type(record).__name__}")
            print(f"   Instrument ID: {record.instrument_id}")
            print(f"   Time: {record.pretty_ts_event}")
            
            # Show all available attributes
            attrs = [attr for attr in dir(record) if not attr.startswith('_') and not callable(getattr(record, attr))]
            for attr in attrs[:10]:  # Show first 10 attributes
                try:
                    value = getattr(record, attr)
                    if attr not in ['hd', 'pretty_ts_event', 'pretty_ts_recv']:  # Skip complex objects
                        print(f"   {attr}: {value}")
                except:
                    pass
    
    print(f"\n📊 SUMMARY:")
    print(f"   Unique Instruments: {len(instruments)}")
    print(f"   Record Types: {dict(record_types)}")
    
    # Now let's try to find ES specifically
    print(f"\n🎯 SEARCHING FOR E-MINI S&P 500 DEFINITIONS...")
    print("-" * 50)
    
    # Search broader date range for ES
    data_broad = client.timeseries.get_range(
        dataset="GLBX.MDP3",
        schema="definition",
        start="2024-12-01",
        end="2025-01-31",
        limit=1000
    )
    
    es_related = []
    all_instruments = set()
    
    for record in data_broad:
        all_instruments.add(record.instrument_id)
        
        # Check if this might be ES related by looking at attributes
        try:
            # Look for any ES-related info in the record
            record_str = str(record).lower()
            if 'es' in record_str or '4916' in str(record.instrument_id):  # 4916 was ES instrument ID from status
                es_related.append(record)
                if len(es_related) <= 3:
                    print(f"\n🎯 Potential ES Record:")
                    print(f"   Instrument ID: {record.instrument_id}")
                    print(f"   Time: {record.pretty_ts_event}")
                    print(f"   Record: {str(record)[:200]}...")
        except:
            pass
    
    print(f"\n📊 BROAD SEARCH RESULTS:")
    print(f"   Total Instruments Found: {len(all_instruments)}")
    print(f"   ES-Related Records: {len(es_related)}")
    print(f"   Sample Instrument IDs: {list(all_instruments)[:20]}")
    
    # Check if instrument 4916 (ES from status) appears in definitions
    if 4916 in all_instruments:
        print(f"✅ Found ES instrument ID 4916 in definitions!")
    else:
        print(f"❌ ES instrument ID 4916 not found in definitions")

if __name__ == "__main__":
    analyze_definition_records() 