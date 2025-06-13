#!/usr/bin/env python3
"""
Comprehensive field analysis for Databento statistics records.
"""

import os
import sys
from datetime import datetime, timedelta

# Add project root to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.ingestion.api_adapters.databento_adapter import DatabentoAdapter

def analyze_all_stats_fields():
    """Comprehensive analysis of all fields in statistics records."""
    
    print("🔍 COMPREHENSIVE STATISTICS FIELD ANALYSIS")
    print("=" * 60)
    
    config = {
        "api": {
            "key_env_var": "DATABENTO_API_KEY"
        }
    }
    
    adapter = DatabentoAdapter(config)
    adapter.connect()
    
    # Get statistics data
    test_job = {
        "dataset": "GLBX.MDP3",
        "schema": "statistics", 
        "symbols": ["ES.c.0"],
        "stype_in": "continuous",
        "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    }
    
    print(f"📊 Fetching statistics data...")
    data_store = adapter._fetch_data_chunk(
        dataset=test_job["dataset"],
        schema=test_job["schema"],
        symbols=test_job["symbols"],
        stype_in=test_job["stype_in"],
        start_date=test_job["start_date"],
        end_date=test_job["end_date"]
    )
    
    # Get first record for analysis
    first_record = None
    for record in data_store:
        first_record = record
        break
    
    if not first_record:
        print("❌ No statistics records found")
        return
    
    print(f"✅ Analyzing record type: {type(first_record).__name__}")
    print(f"📋 Record class: {first_record.__class__}")
    
    # Comprehensive field analysis
    print(f"\n📊 ALL AVAILABLE FIELDS:")
    print("=" * 60)
    
    all_attributes = dir(first_record)
    data_fields = []
    method_fields = []
    private_fields = []
    
    for attr in all_attributes:
        if attr.startswith('_'):
            private_fields.append(attr)
        elif callable(getattr(first_record, attr)):
            method_fields.append(attr)
        else:
            data_fields.append(attr)
    
    print(f"\n📈 DATA FIELDS ({len(data_fields)} total):")
    print("-" * 40)
    
    for field in sorted(data_fields):
        value = getattr(first_record, field)
        field_type = type(value).__name__
        
        # Provide field descriptions
        description = get_field_description(field)
        formatted_value = format_field_value(field, value)
        
        print(f"  🔹 {field:<20} : {formatted_value}")
        print(f"     Type: {field_type:<15} | {description}")
        print()
    
    print(f"\n🛠️  HELPER METHODS ({len(method_fields)} total):")
    print("-" * 40)
    for method in sorted(method_fields):
        description = get_method_description(method)
        print(f"  🔧 {method:<20} : {description}")
    
    print(f"\n🔒 PRIVATE FIELDS ({len(private_fields)} total):")
    print("-" * 40)
    for field in sorted(private_fields):
        print(f"  🔐 {field}")
    
    # Show record header details
    if hasattr(first_record, 'hd'):
        print(f"\n📋 RECORD HEADER DETAILS:")
        print("-" * 40)
        header = first_record.hd
        for attr in dir(header):
            if not attr.startswith('_') and not callable(getattr(header, attr)):
                value = getattr(header, attr)
                print(f"  🔹 hd.{attr:<15} : {value}")
    
    adapter.disconnect()

def get_field_description(field_name):
    """Get human-readable description for each field."""
    descriptions = {
        'channel_id': 'Data channel identifier',
        'hd': 'Record header with metadata',
        'instrument_id': 'Unique instrument identifier',
        'pretty_price': 'Human-readable price (scaled)',
        'pretty_ts_event': 'Human-readable event timestamp', 
        'pretty_ts_recv': 'Human-readable receive timestamp',
        'pretty_ts_ref': 'Human-readable reference timestamp',
        'price': 'Raw price value (scaled by 1e-9)',
        'publisher_id': 'Data publisher/venue identifier',
        'quantity': 'Quantity/volume value',
        'rtype': 'Record type identifier',
        'sequence': 'Message sequence number',
        'size_hint': 'Record size hint for parsing',
        'stat_flags': 'Statistical flags and metadata',
        'stat_type': 'Type of statistic (1=Open, 3=Settlement, 8=Open Interest, etc.)',
        'ts_event': 'Event timestamp (nanoseconds since epoch)',
        'ts_in_delta': 'Time delta for processing',
        'ts_recv': 'Receive timestamp (nanoseconds since epoch)',
        'ts_ref': 'Reference timestamp (nanoseconds since epoch)',
        'update_action': 'Update action (1=Add, 2=Delete)'
    }
    return descriptions.get(field_name, 'Field description not available')

def get_method_description(method_name):
    """Get description for methods."""
    method_descriptions = {
        '__bytes__': 'Convert record to bytes',
        '__str__': 'String representation',
        '__repr__': 'Debug representation', 
        '__eq__': 'Equality comparison',
        '__hash__': 'Hash value for the record',
        '__getstate__': 'Get state for pickling',
        '__sizeof__': 'Memory size of record'
    }
    return method_descriptions.get(method_name, 'Method for record operations')

def format_field_value(field_name, value):
    """Format field values for better readability."""
    if field_name in ['ts_event', 'ts_recv', 'ts_ref']:
        if value == 18446744073709551615:  # Max uint64
            return "N/A (empty timestamp)"
        try:
            dt = datetime.fromtimestamp(value / 1e9)
            return f"{value} ({dt})"
        except:
            return str(value)
    elif field_name == 'price':
        if value == 9223372036854775807:  # Max int64
            return "N/A (empty price)"
        try:
            scaled_price = value / 1e9
            return f"{value} (${scaled_price:.2f})"
        except:
            return str(value)
    elif field_name == 'quantity':
        if value == 2147483647:  # Max int32
            return "N/A (empty quantity)"
        return f"{value:,}"
    elif field_name == 'stat_type':
        stat_names = {
            1: "Opening Price", 2: "Indicative Opening", 3: "Settlement Price",
            4: "Session High", 5: "Session Low", 6: "Session VWAP",
            7: "Clearing Price", 8: "Open Interest", 9: "Open Interest",
            10: "Fixing Price", 11: "Close Price", 12: "Net Change",
            13: "VWAP", 14: "Official Settlement", 15: "Previous Settlement"
        }
        stat_name = stat_names.get(value, f"Unknown ({value})")
        return f"{value} ({stat_name})"
    elif field_name == 'update_action':
        actions = {1: "Add/New", 2: "Delete", 3: "Modify"}
        action_name = actions.get(value, f"Unknown ({value})")
        return f"{value} ({action_name})"
    elif field_name == 'rtype':
        return f"{value} (Record Type)"
    else:
        return str(value)

def show_databento_schema_reference():
    """Show the official Databento schema reference."""
    print(f"\n📚 DATABENTO STATISTICS SCHEMA REFERENCE:")
    print("=" * 60)
    print("""
The Statistics schema provides official venue-published summary statistics:

KEY STATISTIC TYPES:
  1  - Opening Price         : Official opening price
  2  - Indicative Opening    : Pre-market indicative price  
  3  - Settlement Price      : Official settlement price
  4  - Session High Price    : Highest price in session
  5  - Session Low Price     : Lowest price in session
  6  - Session VWAP         : Volume-weighted average price
  7  - Clearing Price       : Clearing/settlement price
  8  - Open Interest        : Total open contracts
  9  - Open Interest        : Alternative open interest
  10 - Fixing Price         : Reference fixing price
  11 - Close Price          : Official closing price
  12 - Net Change           : Price change from previous
  13 - VWAP                 : Volume-weighted average
  14 - Official Settlement  : Final settlement price
  15 - Previous Settlement  : Prior day settlement

TIMESTAMP FIELDS:
  • ts_event : When the statistic was generated/published
  • ts_recv  : When the data was received by Databento
  • ts_ref   : Reference time for the statistic (if applicable)

VALUE FIELDS:
  • price    : For price-based statistics (scaled by 1e-9)
  • quantity : For volume/quantity-based statistics (contracts)
  
METADATA:
  • stat_flags    : Additional statistic metadata
  • update_action : Whether this is new (1) or delete (2)
  • sequence      : Message ordering sequence number
""")

if __name__ == "__main__":
    print("🔍 Statistics Field Analyzer")
    print("=" * 40)
    
    api_key = os.getenv("DATABENTO_API_KEY")
    if not api_key:
        print("❌ DATABENTO_API_KEY not set!")
        exit(1)
    
    analyze_all_stats_fields()
    show_databento_schema_reference() 