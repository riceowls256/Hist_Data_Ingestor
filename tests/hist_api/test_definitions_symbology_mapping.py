#!/usr/bin/env python3
"""
Definition Schema Symbology Mapping Test
Use symbology API to find correct symbol formats for definition schema
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

import databento as db

def test_symbology_for_definitions():
    """Use symbology API to find working symbol formats for definitions"""
    print("🔍 USING SYMBOLOGY API TO FIND DEFINITION SYMBOLS")
    print("="*60)
    
    client = db.Historical()
    print("✅ Connected to Databento API")
    
    # Test symbology resolution for different input types
    print("\n📊 Step 1: Resolve ES.c.0 to different output types")
    print("-" * 50)
    
    output_types = [
        "instrument_id",
        "raw_symbol", 
        "parent",
        "symbol"
    ]
    
    symbol_mappings = {}
    
    for output_type in output_types:
        try:
            print(f"🔍 Resolving ES.c.0 → {output_type}")
            
            result = client.symbology.resolve(
                dataset="GLBX.MDP3",
                symbols=["ES.c.0"],
                stype_in="continuous",
                stype_out=output_type,
                start_date="2024-12-01"
            )
            
            print(f"   Result type: {type(result)}")
            
            if hasattr(result, '__iter__'):
                mappings = list(result)
                print(f"   Found {len(mappings)} mappings:")
                
                for mapping in mappings:
                    print(f"   📋 Mapping:")
                    print(f"      Input: {mapping.input_symbol}")
                    print(f"      Output: {mapping.output_symbol}")
                    print(f"      Start: {mapping.start_date}")
                    print(f"      End: {mapping.end_date}")
                    
                    # Store for testing
                    symbol_mappings[output_type] = mapping.output_symbol
            else:
                print(f"   Single result: {result}")
                symbol_mappings[output_type] = str(result)
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Now test these mapped symbols with definition schema
    print(f"\n📊 Step 2: Testing mapped symbols with definition schema")
    print("-" * 50)
    
    successful_symbols = []
    
    for symbol_type, symbol_value in symbol_mappings.items():
        try:
            print(f"🔍 Testing {symbol_type}: {symbol_value}")
            
            data = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                schema="definition",
                symbols=[symbol_value],
                start="2024-12-01",
                end="2024-12-02",
                limit=10
            )
            
            record_count = 0
            for record in data:
                record_count += 1
                if record_count == 1:  # Show first record details
                    print(f"   📋 First Record:")
                    print(f"      Instrument ID: {record.instrument_id}")
                    print(f"      Raw Symbol: {getattr(record, 'raw_symbol', 'N/A')}")
                    print(f"      Asset: {getattr(record, 'asset', 'N/A')}")
                    print(f"      Time: {record.pretty_ts_event}")
                    
            if record_count > 0:
                print(f"   ✅ SUCCESS: {record_count} records found!")
                successful_symbols.append((symbol_type, symbol_value, record_count))
            else:
                print(f"   ❌ No records found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test reverse approach - find symbols that map to instrument 4916
    print(f"\n📊 Step 3: Find symbols that map to instrument ID 4916")
    print("-" * 50)
    
    try:
        # Reverse lookup - what symbols map to instrument 4916?
        result = client.symbology.resolve(
            dataset="GLBX.MDP3",
            symbols=["4916"],
            stype_in="instrument_id",
            stype_out="raw_symbol",
            start_date="2024-12-01"
        )
        
        print("🔍 Symbols that map to instrument 4916:")
        raw_symbols = []
        
        for mapping in result:
            print(f"   📋 {mapping.input_symbol} → {mapping.output_symbol}")
            print(f"      Start: {mapping.start_date}, End: {mapping.end_date}")
            raw_symbols.append(mapping.output_symbol)
        
        # Test these raw symbols with definition schema
        for raw_symbol in raw_symbols[:3]:  # Test first 3
            try:
                print(f"\n🔍 Testing raw symbol: {raw_symbol}")
                
                data = client.timeseries.get_range(
                    dataset="GLBX.MDP3", 
                    schema="definition",
                    symbols=[raw_symbol],
                    start="2024-12-01",
                    end="2024-12-02",
                    limit=5
                )
                
                count = sum(1 for _ in data)
                if count > 0:
                    print(f"   ✅ SUCCESS with {raw_symbol}: {count} records!")
                    successful_symbols.append(("raw_symbol", raw_symbol, count))
                else:
                    print(f"   ❌ No records with {raw_symbol}")
                    
            except Exception as e:
                print(f"   ❌ Error with {raw_symbol}: {e}")
                
    except Exception as e:
        print(f"❌ Reverse lookup failed: {e}")
    
    # Final test - try other datasets
    print(f"\n📊 Step 4: Test definition schema on other datasets")
    print("-" * 50)
    
    other_datasets = [
        "XNAS.ITCH",
        "DBEQ.BASIC",
        "GLBX.MDP3"  # But with different symbols
    ]
    
    for dataset in other_datasets:
        try:
            print(f"🔍 Testing dataset: {dataset}")
            
            # Try a simple query without symbols to see if schema exists
            data = client.timeseries.get_range(
                dataset=dataset,
                schema="definition",
                start="2024-12-01",
                end="2024-12-02", 
                limit=1
            )
            
            count = sum(1 for _ in data)
            print(f"   Dataset {dataset}: {count} records (no symbol filter)")
            
        except Exception as e:
            print(f"   Dataset {dataset}: Error - {e}")
    
    # Summary
    print(f"\n🎯 FINAL RESULTS")
    print("="*50)
    
    if successful_symbols:
        print("✅ SUCCESSFUL SYMBOL FORMATS FOUND:")
        for symbol_type, symbol_value, count in successful_symbols:
            print(f"   • {symbol_type}: '{symbol_value}' → {count} records")
    else:
        print("❌ NO WORKING SYMBOL FORMATS FOUND")
        print("   → Definition schema may not support symbol filtering")
        print("   → Manual filtering approach appears to be the only solution")
        print("   → Or definition schema may work differently than other schemas")

if __name__ == "__main__":
    test_symbology_for_definitions() 