#!/usr/bin/env python3
"""
Test CME Globex MDP 3.0 specific statistics based on publisher availability.
"""

import os
import sys
from datetime import datetime, timedelta

# Add project root to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.ingestion.api_adapters.databento_adapter import DatabentoAdapter

def test_cme_globex_statistics():
    """Test statistics available for CME Globex MDP 3.0 (GLBX.MDP3)."""
    
    print("🏛️ CME GLOBEX MDP 3.0 STATISTICS TEST")
    print("=" * 60)
    print("Testing statistics available for CME Globex publisher")
    
    # Based on the publisher table, CME Globex MDP 3.0 supports:
    cme_expected_stats = {
        1: "Opening price",
        2: "Indicative opening price", 
        3: "Settlement price",
        4: "Trading session high price",
        5: "Trading session low price",
        6: "Cleared volume",
        7: "Lowest offer",
        8: "Highest bid", 
        9: "Open interest",
        10: "Fixing price"
    }
    
    print(f"\n📊 Expected CME Globex Statistics ({len(cme_expected_stats)}):")
    for stat_type, description in cme_expected_stats.items():
        print(f"   {stat_type:2d} - {description}")
    
    config = {
        "api": {
            "key_env_var": "DATABENTO_API_KEY"
        }
    }
    
    adapter = DatabentoAdapter(config)
    adapter.connect()
    
    # Extended date range to capture more statistics types
    test_job = {
        "dataset": "GLBX.MDP3",         # CME Globex dataset
        "schema": "statistics",
        "symbols": ["ES.c.0"],
        "stype_in": "continuous",
        "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),  # 30 days
        "end_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    }
    
    print(f"\n🔍 Fetching 30 days of statistics data...")
    print(f"📅 Date range: {test_job['start_date']} to {test_job['end_date']}")
    
    data_store = adapter._fetch_data_chunk(
        dataset=test_job["dataset"],
        schema=test_job["schema"],
        symbols=test_job["symbols"],
        stype_in=test_job["stype_in"],
        start_date=test_job["start_date"],
        end_date=test_job["end_date"]
    )
    
    # Analyze what statistics we actually found
    found_stats = {}
    total_records = 0
    
    for record in data_store:
        total_records += 1
        if hasattr(record, 'stat_type'):
            stat_type = record.stat_type
            if stat_type not in found_stats:
                found_stats[stat_type] = []
            
            # Store sample record info
            record_info = {
                'timestamp': datetime.fromtimestamp(record.ts_event / 1e9),
                'price': record.price / 1e9 if record.price != 9223372036854775807 else None,
                'quantity': record.quantity if record.quantity != 2147483647 else None,
                'update_action': record.update_action
            }
            found_stats[stat_type].append(record_info)
    
    print(f"\n✅ Found {total_records} total statistics records")
    
    # Compare expected vs found
    print(f"\n📊 STATISTICS AVAILABILITY ANALYSIS:")
    print("=" * 60)
    
    print(f"\n✅ FOUND Statistics:")
    for stat_type in sorted(found_stats.keys()):
        count = len(found_stats[stat_type])
        description = cme_expected_stats.get(stat_type, f"Unknown stat type {stat_type}")
        print(f"   {stat_type:2d} - {description:<30} ({count:,} records)")
        
        # Show sample data
        if found_stats[stat_type]:
            sample = found_stats[stat_type][0]
            sample_str = ""
            if sample['price']:
                sample_str += f"${sample['price']:.2f}"
            if sample['quantity']:
                sample_str += f" | {sample['quantity']:,} contracts"
            if sample_str:
                print(f"       Sample: {sample_str} at {sample['timestamp'].date()}")
    
    print(f"\n❌ NOT FOUND Statistics (may be published at different times):")
    for stat_type, description in cme_expected_stats.items():
        if stat_type not in found_stats:
            print(f"   {stat_type:2d} - {description}")
    
    # Analysis by date to see patterns
    print(f"\n📅 STATISTICS BY DATE (last 7 days):")
    print("-" * 40)
    
    daily_stats = {}
    for stat_type, records in found_stats.items():
        for record in records:
            date = record['timestamp'].date()
            if date not in daily_stats:
                daily_stats[date] = set()
            daily_stats[date].add(stat_type)
    
    # Show recent days
    recent_dates = sorted(daily_stats.keys())[-7:]  # Last 7 days
    for date in recent_dates:
        stat_types = sorted(daily_stats[date])
        stat_names = [cme_expected_stats.get(st, f"Type {st}") for st in stat_types]
        print(f"   {date}: {stat_types} ({', '.join(stat_names)})")
    
    adapter.disconnect()
    return found_stats

def analyze_settlement_patterns():
    """Specifically look for settlement price patterns."""
    
    print(f"\n🔍 SETTLEMENT PRICE ANALYSIS:")
    print("=" * 40)
    
    config = {
        "api": {
            "key_env_var": "DATABENTO_API_KEY"
        }
    }
    
    adapter = DatabentoAdapter(config)
    adapter.connect()
    
    # Look further back for settlement prices (they're typically end-of-day)
    test_job = {
        "dataset": "GLBX.MDP3",
        "schema": "statistics",
        "symbols": ["ES.c.0"],
        "stype_in": "continuous",
        "start_date": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),  # 60 days
        "end_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    }
    
    print(f"🔍 Extended search for settlement prices (60 days)...")
    
    data_store = adapter._fetch_data_chunk(
        dataset=test_job["dataset"],
        schema=test_job["schema"],
        symbols=test_job["symbols"],
        stype_in=test_job["stype_in"],
        start_date=test_job["start_date"],
        end_date=test_job["end_date"]
    )
    
    settlement_records = []
    for record in data_store:
        if hasattr(record, 'stat_type') and record.stat_type == 3:  # Settlement price
            settlement_records.append({
                'date': datetime.fromtimestamp(record.ts_event / 1e9).date(),
                'time': datetime.fromtimestamp(record.ts_event / 1e9).time(),
                'price': record.price / 1e9 if record.price != 9223372036854775807 else None
            })
    
    if settlement_records:
        print(f"✅ Found {len(settlement_records)} settlement price records!")
        for i, record in enumerate(settlement_records[:10]):  # Show first 10
            print(f"   {i+1}. {record['date']} at {record['time']}: ${record['price']:.2f}")
    else:
        print("❌ No settlement prices found in 60-day period")
        print("   Settlement prices may be published less frequently or at specific times")
    
    adapter.disconnect()
    return len(settlement_records)

if __name__ == "__main__":
    print("🏛️ CME Globex Statistics Publisher Test")
    print("=" * 50)
    
    api_key = os.getenv("DATABENTO_API_KEY")
    if not api_key:
        print("❌ DATABENTO_API_KEY not set!")
        exit(1)
    
    # Test CME-specific statistics
    found_stats = test_cme_globex_statistics()
    
    # Specific settlement price analysis
    settlement_count = analyze_settlement_patterns()
    
    print(f"\n🎯 SUMMARY:")
    print(f"   Statistics types found: {len(found_stats)}/10 expected for CME")
    print(f"   Settlement prices found: {settlement_count}")
    print(f"   Dataset: GLBX.MDP3 (CME Globex MDP 3.0) ✅") 