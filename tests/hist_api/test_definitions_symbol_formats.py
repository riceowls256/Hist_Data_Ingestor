#!/usr/bin/env python3
"""
Definition Schema Symbol Format Testing
Testing different symbol formats to find what works with definition schema
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

import databento as db
from datetime import datetime

def test_symbol_formats():
    """Test different symbol formats to see what works with definition schema"""
    print("🔍 TESTING SYMBOL FORMATS FOR DEFINITION SCHEMA")
    print("="*60)
    
    client = db.Historical()
    print("✅ Connected to Databento API")
    
    # Different symbol formats to try
    symbol_formats = {
        "Continuous Front Month": ["ES.c.0"],
        "Specific Contract Months": [
            "ESM5",   # June 2025 (from our successful manual search)
            "ESH25",  # March 2025
            "ESU25",  # September 2025
            "ESZ25",  # December 2025
        ],
        "Alternative Continuous": [
            "ES.c.1",  # Second month
            "ES.c.2",  # Third month
        ],
        "Legacy/Alternative Formats": [
            "ES.FUT",
            "ES",
            "ES1!",
            "ESM2025",
        ],
        "Instrument ID as Symbol": [
            "4916",  # Direct instrument ID
        ],
        "Multiple Symbols": [
            ["ES.c.0", "CL.c.0"],  # Test multiple at once
            ["ESM5", "ESU5"],      # Multiple specific contracts
        ]
    }
    
    successful_formats = []
    
    for category, symbol_list in symbol_formats.items():
        print(f"\n📊 Testing {category}")
        print("-" * 50)
        
        for symbols in symbol_list:
            try:
                # Handle both single symbols and lists
                if isinstance(symbols, list):
                    symbol_display = str(symbols)
                    test_symbols = symbols
                else:
                    symbol_display = symbols
                    test_symbols = [symbols]
                
                print(f"🔍 Testing: {symbol_display}")
                
                data = client.timeseries.get_range(
                    dataset="GLBX.MDP3",
                    schema="definition",
                    symbols=test_symbols,
                    start="2024-12-01",
                    end="2024-12-02",  # Short date range for quick testing
                    limit=10  # Just get a few records to test
                )
                
                record_count = 0
                sample_records = []
                
                for record in data:
                    record_count += 1
                    if record_count <= 3:  # Keep first 3 for analysis
                        sample_records.append(record)
                    if record_count >= 10:  # Stop after 10 for efficiency
                        break
                
                if record_count > 0:
                    print(f"   ✅ SUCCESS: {record_count} records found!")
                    successful_formats.append({
                        'symbols': test_symbols,
                        'count': record_count,
                        'category': category
                    })
                    
                    # Show sample record details
                    for i, record in enumerate(sample_records):
                        print(f"   📋 Sample Record {i+1}:")
                        print(f"      Instrument ID: {record.instrument_id}")
                        print(f"      Time: {record.pretty_ts_event}")
                        if hasattr(record, 'raw_symbol'):
                            print(f"      Raw Symbol: {record.raw_symbol}")
                        if hasattr(record, 'asset'):
                            print(f"      Asset: {record.asset}")
                        if hasattr(record, 'exchange'):
                            print(f"      Exchange: {record.exchange}")
                        print()
                else:
                    print(f"   ❌ No records: {symbol_display}")
                    
            except Exception as e:
                print(f"   ❌ Error with {symbol_display}: {e}")
                # Handle specific error types
                if "schema_not_supported" in str(e):
                    print(f"      → Schema not supported")
                elif "symbology_invalid_request" in str(e):
                    print(f"      → Invalid symbol format")
                elif "not a valid value of Schema" in str(e):
                    print(f"      → Schema validation error")
                else:
                    print(f"      → Unknown error type")
    
    # Summary of successful formats
    print(f"\n🎯 SUCCESSFUL SYMBOL FORMATS SUMMARY")
    print("="*50)
    
    if successful_formats:
        for success in successful_formats:
            print(f"✅ {success['symbols']} ({success['category']}): {success['count']} records")
        
        print(f"\n📊 BEST PRACTICES:")
        print("Based on successful formats:")
        for success in successful_formats:
            if success['count'] > 0:
                print(f"   • Use {success['symbols']} format for {success['category'].lower()}")
    else:
        print("❌ No symbol formats worked with definition schema")
        print("   → May need to use the manual filtering approach")
        print("   → Or definition schema may not support symbol filtering at all")
    
    # Test a few more alternative approaches
    print(f"\n🔬 TESTING ALTERNATIVE APPROACHES")
    print("-" * 50)
    
    # Test with no date filter
    try:
        print("🔍 Testing without date filter...")
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            schema="definition",
            symbols=["ES.c.0"],
            limit=5
        )
        count = sum(1 for _ in data)
        print(f"   No date filter: {count} records")
    except Exception as e:
        print(f"   No date filter failed: {e}")
    
    # Test with different date ranges
    date_ranges = [
        ("2025-01-01", "2025-01-02"),  # Future dates
        ("2023-01-01", "2023-01-02"),  # Older dates
        ("2024-06-01", "2024-06-02"),  # Middle of year
    ]
    
    for start, end in date_ranges:
        try:
            print(f"🔍 Testing date range {start} to {end}...")
            data = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                schema="definition",
                symbols=["ES.c.0"],
                start=start,
                end=end,
                limit=5
            )
            count = sum(1 for _ in data)
            print(f"   {start}-{end}: {count} records")
        except Exception as e:
            print(f"   {start}-{end} failed: {e}")

if __name__ == "__main__":
    test_symbol_formats() 