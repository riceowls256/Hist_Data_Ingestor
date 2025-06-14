#!/usr/bin/env python3
"""
Test script for Databento definitions schema.
Explores instrument definitions and metadata structure.
"""

import os
import sys
from datetime import datetime, timedelta

# Add project root to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.ingestion.api_adapters.databento_adapter import DatabentoAdapter
from src.utils.custom_logger import get_logger

logger = get_logger(__name__)

# CONFIGURATION - Change these to test different instruments
SYMBOL = "ES.c.0"  # E-mini S&P 500 continuous front month
DATASET = "GLBX.MDP3"  # CME dataset
CONTRACT_NAME = "E-mini S&P 500"  # Human-readable name

def test_schema_availability():
    """Test different possible schema names for definitions."""
    
    print(f"\n🔍 TESTING AVAILABLE SCHEMAS FOR DEFINITIONS")
    print("=" * 60)
    
    config = {
        "api": {
            "key_env_var": "DATABENTO_API_KEY"
        }
    }
    
    # Try different possible schema names
    possible_schemas = [
        "definition",
        "mbo",
        "symbology", 
        "imbalance",
        "status"
    ]
    
    adapter = DatabentoAdapter(config)
    adapter.connect()
    
    schema_results = {}
    
    for schema in possible_schemas:
        print(f"\n📋 Testing schema: {schema}")
        try:
            test_job = {
                "dataset": DATASET,
                "schema": schema,
                "symbols": [SYMBOL],
                "stype_in": "continuous",
                "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                "end_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            }
            
            data_store = adapter._fetch_data_chunk(
                dataset=test_job["dataset"],
                schema=test_job["schema"],
                symbols=test_job["symbols"],
                stype_in=test_job["stype_in"],
                start_date=test_job["start_date"],
                end_date=test_job["end_date"]
            )
            
            record_count = sum(1 for _ in data_store)
            schema_results[schema] = record_count
            print(f"   ✅ {schema}: {record_count} records")
            
        except Exception as e:
            schema_results[schema] = f"Error: {str(e)[:100]}"
            print(f"   ❌ {schema}: {str(e)[:100]}")
    
    adapter.disconnect()
    
    print(f"\n📊 SCHEMA AVAILABILITY SUMMARY:")
    print("=" * 40)
    for schema, result in schema_results.items():
        print(f"   {schema:<12}: {result}")
    
    return schema_results

def test_definitions_schema(symbol=SYMBOL, dataset=DATASET, contract_name=CONTRACT_NAME):
    """Test definitions schema for instrument metadata using UTC midnight snapshots."""
    
    print(f"🔍 TESTING DEFINITIONS SCHEMA FOR {contract_name} ({symbol})")
    print("=" * 70)
    
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
        
        # Use UTC midnight snapshots as recommended by Databento
        # Try multiple Monday UTC midnight periods for better chances of finding definitions
        test_periods = [
            # Recent Monday UTC midnight (more likely to have current definitions)
            (datetime.now() - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0),
            # Previous Monday UTC midnight  
            (datetime.now() - timedelta(days=14)).replace(hour=0, minute=0, second=0, microsecond=0),
            # Go back further for contract rollover periods (more definition changes)
            (datetime.now() - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0),
        ]
        
        total_records = 0
        all_sample_records = []
        
        for i, start_time in enumerate(test_periods, 1):
            end_time = start_time + timedelta(days=1)  # 24-hour period as recommended
            
            test_job = {
                "dataset": dataset,
                "schema": "definition",           # Definitions schema
                "symbols": [symbol],
                "stype_in": "continuous",        # Continuous contract
                "start_date": start_time.strftime("%Y-%m-%d"),
                "end_date": end_time.strftime("%Y-%m-%d")
            }
            
            print(f"\n📊 Test Period {i}: UTC Midnight Snapshot")
            print(f"📅 Start: {start_time} UTC")
            print(f"📅 End: {end_time} UTC")
            
            # Fetch definitions data for this period
            print(f"🔍 Fetching {contract_name} definitions...")
            data_store = adapter._fetch_data_chunk(
                dataset=test_job["dataset"],
                schema=test_job["schema"],
                symbols=test_job["symbols"],
                stype_in=test_job["stype_in"],
                start_date=test_job["start_date"],
                end_date=test_job["end_date"]
            )
            
            # Count records for this period
            period_records = 0
            period_samples = []
            
            for record in data_store:
                period_records += 1
                total_records += 1
                if len(period_samples) < 2:  # Keep samples from each period
                    period_samples.append(record)
                if period_records >= 20:  # Don't process too many per period
                    break
            
            print(f"📊 Period {i} Results: {period_records} definition records")
            
            if period_samples:
                all_sample_records.extend(period_samples)
                # Show key info for this period
                first_record = period_samples[0]
                if hasattr(first_record, 'ts_event'):
                    timestamp = datetime.fromtimestamp(first_record.ts_event / 1e9)
                    print(f"📅 First definition timestamp: {timestamp} UTC")
                
                if hasattr(first_record, 'raw_symbol'):
                    print(f"📛 Raw symbol: {first_record.raw_symbol}")
            
            # If we found definitions, we can stop searching earlier periods
            if period_records > 0:
                print(f"✅ Found definitions in period {i}, analyzing...")
                break
        
        print(f"\n✅ Total definition records found: {total_records}")
        
        if all_sample_records:
            print(f"\n📋 {contract_name} DEFINITIONS ANALYSIS:")
            print("=" * 50)
            
            # Analyze first record in detail
            first_record = all_sample_records[0]
            print(f"📄 Record type: {type(first_record).__name__}")
            print(f"📄 Record class: {first_record.__class__}")
            
            # Show key definition fields
            analyze_definition_fields(first_record, contract_name)
            
            # Show point-in-time analysis
            analyze_point_in_time_definitions(all_sample_records, contract_name)
            
            # Show all available attributes for reference
            print(f"\n🔍 ALL AVAILABLE FIELDS:")
            print("-" * 40)
            all_attributes = []
            for attr in dir(first_record):
                if not attr.startswith('_') and not callable(getattr(first_record, attr)):
                    value = getattr(first_record, attr)
                    all_attributes.append((attr, value, type(value).__name__))
            
            # Sort and display key attributes only (first 15)
            for attr, value, value_type in sorted(all_attributes)[:15]:
                description = get_definition_field_description(attr)
                formatted_value = format_definition_value(attr, value)
                print(f"  🔹 {attr:<25} : {formatted_value}")
                print(f"     Type: {value_type:<15} | {description}")
                print()
            
            print(f"   ... and {len(all_attributes) - 15} more fields")
        
        else:
            print(f"\n⚠️  No definition records found for {contract_name}")
            print(f"   This could mean:")
            print(f"   • Contract definitions haven't changed recently")
            print(f"   • Different symbol format needed")
            print(f"   • Longer historical period required")
        
        adapter.disconnect()
        print(f"\n🎉 {contract_name} ({symbol}) Definitions Test COMPLETED!")
        print(f"   Dataset: {dataset} ✅")
        print(f"   Schema: definition ✅")
        print(f"   Records: {total_records} ✅")
        
        return True
        
    except Exception as e:
        print(f"❌ {contract_name} ({symbol}) Definitions Test FAILED: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

def analyze_definition_fields(record, contract_name):
    """Analyze key definition fields in detail."""
    
    print(f"\n📊 KEY DEFINITION FIELDS FOR {contract_name}:")
    print("-" * 40)
    
    # Basic identification
    if hasattr(record, 'instrument_id'):
        print(f"🏷️  Instrument ID: {record.instrument_id}")
    
    if hasattr(record, 'raw_symbol'):
        print(f"📛 Raw Symbol: {record.raw_symbol}")
    
    if hasattr(record, 'ts_event'):
        timestamp = datetime.fromtimestamp(record.ts_event / 1e9)
        print(f"📅 Event Time: {timestamp}")
    
    # Contract specifications
    if hasattr(record, 'security_type'):
        print(f"📋 Security Type: {record.security_type}")
    
    if hasattr(record, 'asset'):
        print(f"💰 Asset: {record.asset}")
    
    if hasattr(record, 'exchange'):
        print(f"🏛️  Exchange: {record.exchange}")
    
    if hasattr(record, 'currency'):
        print(f"💵 Currency: {record.currency}")
    
    # Trading parameters
    if hasattr(record, 'min_price_increment'):
        tick_size = record.min_price_increment / 1e9  # Scale by 1e-9
        print(f"📏 Tick Size: ${tick_size}")
    
    if hasattr(record, 'contract_multiplier'):
        print(f"🔢 Contract Multiplier: {record.contract_multiplier}")
    
    if hasattr(record, 'min_lot_size'):
        print(f"📦 Min Lot Size: {record.min_lot_size}")
    
    # Contract lifecycle
    if hasattr(record, 'expiration'):
        if record.expiration != 18446744073709551615:  # Not max uint64
            exp_date = datetime.fromtimestamp(record.expiration / 1e9)
            print(f"📆 Expiration: {exp_date}")
    
    if hasattr(record, 'activation'):
        if record.activation != 18446744073709551615:  # Not max uint64  
            act_date = datetime.fromtimestamp(record.activation / 1e9)
            print(f"🟢 Activation: {act_date}")

def get_definition_field_description(field_name):
    """Get human-readable description for definition fields."""
    descriptions = {
        'instrument_id': 'Unique instrument identifier',
        'raw_symbol': 'Native exchange symbol',
        'ts_event': 'Definition event timestamp',
        'ts_recv': 'Data receive timestamp',
        'security_type': 'Type of security (FUT, OPT, etc.)',
        'asset': 'Underlying asset class',
        'exchange': 'Trading exchange code',
        'currency': 'Base currency for instrument',
        'min_price_increment': 'Minimum tick size (scaled by 1e-9)',
        'contract_multiplier': 'Contract size multiplier',
        'min_lot_size': 'Minimum order size',
        'expiration': 'Contract expiration timestamp',
        'activation': 'Contract activation timestamp',
        'high_limit_price': 'Upper price limit (scaled by 1e-9)',
        'low_limit_price': 'Lower price limit (scaled by 1e-9)',
        'security_group': 'Security group classification',
        'instrument_class': 'Instrument class code',
        'display_factor': 'Price display scaling factor',
        'max_trade_vol': 'Maximum trade volume',
        'settlement_currency': 'Settlement currency',
        'underlying': 'Underlying instrument symbol',
        'strike_price': 'Option strike price (scaled by 1e-9)',
        'maturity_year': 'Contract maturity year',
        'maturity_month': 'Contract maturity month',
        'unit_of_measure': 'Unit of measure for quantity'
    }
    return descriptions.get(field_name, 'Definition field')

def format_definition_value(field_name, value):
    """Format definition values for better readability."""
    if field_name in ['ts_event', 'ts_recv', 'expiration', 'activation']:
        if value == 18446744073709551615:  # Max uint64
            return "N/A (not set)"
        try:
            dt = datetime.fromtimestamp(value / 1e9)
            return f"{value} ({dt})"
        except:
            return str(value)
    elif field_name in ['min_price_increment', 'high_limit_price', 'low_limit_price', 'strike_price']:
        if value == 9223372036854775807:  # Max int64
            return "N/A (not set)"
        try:
            scaled_price = value / 1e9
            return f"{value} (${scaled_price})"
        except:
            return str(value)
    elif field_name in ['max_trade_vol', 'min_lot_size']:
        if value == 9223372036854775807 or value == 2147483647:  # Max values
            return "N/A (unlimited)"
        return f"{value:,}"
    elif field_name == 'security_type':
        security_types = {
            'FUT': 'Futures',
            'OPT': 'Options', 
            'STK': 'Stock',
            'ETF': 'ETF',
            'IDX': 'Index'
        }
        return f"'{value}' ({security_types.get(value, 'Unknown')})"
    else:
        return str(value)

def analyze_point_in_time_definitions(records, contract_name):
    """Analyze point-in-time aspects of definition records."""
    
    print(f"\n⏰ POINT-IN-TIME DEFINITION ANALYSIS:")
    print("-" * 40)
    
    timestamps = []
    for record in records:
        if hasattr(record, 'ts_event'):
            timestamp = datetime.fromtimestamp(record.ts_event / 1e9)
            timestamps.append(timestamp)
    
    if timestamps:
        print(f"📅 Time range: {min(timestamps)} to {max(timestamps)} UTC")
        print(f"⏱️  Time span: {max(timestamps) - min(timestamps)}")
        print(f"📊 Definition updates: {len(timestamps)} records")
        
        # Show each timestamp
        for i, ts in enumerate(timestamps[:5], 1):  # Show first 5
            print(f"   {i}. {ts} UTC")
        
        if len(timestamps) > 5:
            print(f"   ... and {len(timestamps) - 5} more timestamps")
    
    # Check for multi-leg strategy records
    leg_records = [r for r in records if hasattr(r, 'leg_index') and r.leg_index is not None]
    if leg_records:
        print(f"\n🔀 MULTI-LEG STRATEGY DETECTED:")
        print(f"   Found {len(leg_records)} leg definition records")
        for i, record in enumerate(leg_records[:3], 1):
            if hasattr(record, 'leg_index'):
                print(f"   Leg {record.leg_index}: {getattr(record, 'leg_raw_symbol', 'N/A')}")

def test_strategy_definitions():
    """Test definitions for multi-leg strategies/spreads."""
    
    print(f"\n🔀 TESTING STRATEGY/SPREAD DEFINITIONS")
    print("=" * 50)
    
    # Test instruments more likely to have strategy definitions
    strategy_symbols = [
        ("ES.c.0", "E-mini S&P 500"),  # May have calendar spreads
        ("ZN.c.0", "10-Year Treasury"), # Interest rate spreads common
    ]
    
    config = {
        "api": {
            "key_env_var": "DATABENTO_API_KEY"
        }
    }
    
    adapter = DatabentoAdapter(config)
    adapter.connect()
    
    for symbol, name in strategy_symbols:
        print(f"\n📊 Testing {name} ({symbol}) for strategy definitions...")
        
        # Look back further for strategy definitions (they change less frequently)
        start_time = (datetime.now() - timedelta(days=60)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=7)  # Week-long period
        
        test_job = {
            "dataset": "GLBX.MDP3",
            "schema": "definition",
            "symbols": [symbol],
            "stype_in": "continuous",
            "start_date": start_time.strftime("%Y-%m-%d"),
            "end_date": end_time.strftime("%Y-%m-%d")
        }
        
        try:
            data_store = adapter._fetch_data_chunk(
                dataset=test_job["dataset"],
                schema=test_job["schema"],
                symbols=test_job["symbols"],
                stype_in=test_job["stype_in"],
                start_date=test_job["start_date"],
                end_date=test_job["end_date"]
            )
            
            strategy_records = []
            for record in data_store:
                strategy_records.append(record)
                if len(strategy_records) >= 10:
                    break
            
            if strategy_records:
                print(f"✅ Found {len(strategy_records)} strategy definition records")
                
                # Look for multi-leg indicators
                multi_leg = [r for r in strategy_records if hasattr(r, 'leg_count') and r.leg_count > 1]
                if multi_leg:
                    print(f"🔀 Multi-leg strategies found: {len(multi_leg)} records")
            else:
                print(f"⚠️  No strategy definitions found for {symbol}")
                
        except Exception as e:
            print(f"❌ Error testing {symbol}: {str(e)[:100]}")
    
    adapter.disconnect()

def test_multiple_instruments():
    """Test definitions schema for multiple instrument types."""
    
    print(f"\n🔍 TESTING DEFINITIONS FOR MULTIPLE INSTRUMENTS")
    print("=" * 60)
    
    # Test different instrument types
    instruments = [
        ("ES.c.0", "GLBX.MDP3", "E-mini S&P 500"),
        ("CL.c.0", "GLBX.MDP3", "Crude Oil WTI"),
        ("GC.c.0", "GLBX.MDP3", "Gold"),
    ]
    
    results = {}
    
    for symbol, dataset, name in instruments:
        print(f"\n📊 Testing {name} ({symbol})...")
        success = test_definitions_schema(symbol, dataset, name)
        results[symbol] = success
    
    print(f"\n📊 MULTI-INSTRUMENT DEFINITIONS TEST SUMMARY:")
    print("=" * 50)
    for symbol, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {symbol}: {status}")
    
    return results

if __name__ == "__main__":
    print("🔍 Databento Definitions Schema Test Suite")
    print("=" * 50)
    
    api_key = os.getenv("DATABENTO_API_KEY")
    if not api_key:
        print("❌ DATABENTO_API_KEY not set!")
        exit(1)
    
    print(f"📊 Testing Symbol: {SYMBOL}")
    print(f"📈 Dataset: {DATASET}")
    print(f"🏷️  Contract: {CONTRACT_NAME}")
    
    # First test schema availability
    print(f"\n🧪 Step 1: Testing schema availability...")
    schema_results = test_schema_availability()
    
    # Find schemas with data
    available_schemas = [schema for schema, result in schema_results.items() 
                        if isinstance(result, int) and result > 0]
    
    if available_schemas:
        print(f"\n✅ Found data in schemas: {available_schemas}")
        print(f"\n🧪 Step 2: Testing definitions schema with UTC midnight snapshots...")
        # Run single instrument test
        success = test_definitions_schema()
        
        print(f"\n🧪 Step 3: Testing strategy/spread definitions...")
        test_strategy_definitions()
        
        if success:
            print(f"\n🎯 Testing multiple instruments...")
            test_multiple_instruments()
        else:
            print(f"\n⚠️  Main definition test completed but found limited data.")
    else:
        print(f"\n⚠️  No definition data found in any tested schemas.")
        print(f"   This might be normal - definitions may be published infrequently")
        print(f"   or may require different datasets/date ranges.")
        print(f"\n🧪 Still testing definitions schema with optimized approach...")
        test_definitions_schema()
    
    print(f"\n✅ All definitions schema tests completed!") 