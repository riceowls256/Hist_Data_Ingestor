#!/usr/bin/env python3
"""
Debug Definition Schema with Parent Symbology
Use parent symbology (ES.FUT) to efficiently get all ES futures and spreads
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

import databento as db
import pandas as pd

def debug_definition_schema():
    """Debug definition schema using parent symbology"""
    print("🔍 DEBUGGING DEFINITION SCHEMA WITH PARENT SYMBOLOGY")
    print("="*60)
    
    client = db.Historical()
    dataset = "GLBX.MDP3"
    date = "2024-12-01"
    
    try:
        # Use parent symbology to get all ES contracts
        print("📡 Requesting ES.FUT definitions with parent symbology...")
        data = client.timeseries.get_range(
            dataset=dataset,
            symbols="ES.FUT",
            start=date,
            stype_in="parent",  # This is key for parent symbology
            schema="definition",
        )
        
        # Convert to DataFrame for easier analysis
        df = data.to_df()
        print(f"✅ Loaded {len(df):,} ES instrument definitions")
        
        # Analyze instrument classes
        print(f"\n📊 INSTRUMENT CLASS BREAKDOWN:")
        class_counts = df['instrument_class'].value_counts()
        for class_name, count in class_counts.items():
            print(f"   {class_name}: {count:,} instruments")
        
        # Filter out spreads to get only outright futures
        futures_df = df[df['instrument_class'] == db.InstrumentClass.FUTURE]
        print(f"\n🎯 OUTRIGHT FUTURES ONLY: {len(futures_df):,} contracts")
        
        # Sort by expiration and show structure
        if not futures_df.empty:
            futures_df = futures_df.set_index('expiration').sort_index()
            print(f"\n📅 FUTURES BY EXPIRATION (First 10):")
            print(futures_df[['instrument_id', 'raw_symbol']].head(10))
            
            # Show expiration range
            min_exp = futures_df.index.min()
            max_exp = futures_df.index.max()
            print(f"\n⏰ EXPIRATION RANGE:")
            print(f"   Earliest: {min_exp}")
            print(f"   Latest: {max_exp}")
        
        # Analyze spreads if any
        spreads_df = df[df['instrument_class'] != db.InstrumentClass.FUTURE]
        if not spreads_df.empty:
            print(f"\n🔄 SPREADS ANALYSIS: {len(spreads_df):,} contracts")
            spread_classes = spreads_df['instrument_class'].value_counts()
            for class_name, count in spread_classes.items():
                print(f"   {class_name}: {count:,} instruments")
            
            # Show sample spreads
            print(f"\n📋 SAMPLE SPREADS (First 5):")
            sample_spreads = spreads_df[['raw_symbol', 'instrument_class', 'instrument_id']].head()
            for _, row in sample_spreads.iterrows():
                print(f"   {row['raw_symbol']} ({row['instrument_class']}) - ID: {row['instrument_id']}")
        
        # Show all available columns for understanding the data structure
        print(f"\n🔍 AVAILABLE DATA COLUMNS:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i:2d}. {col}")
        
        # Check for any additional useful fields
        print(f"\n💡 SAMPLE RECORD DETAILS:")
        if not df.empty:
            sample_record = df.iloc[0]
            print(f"   Symbol: {sample_record.get('raw_symbol', 'N/A')}")
            print(f"   Asset: {sample_record.get('asset', 'N/A')}")
            print(f"   Security Type: {sample_record.get('security_type', 'N/A')}")
            print(f"   Min Price Increment: {sample_record.get('min_price_increment', 'N/A')}")
            print(f"   Currency: {sample_record.get('currency', 'N/A')}")
            print(f"   Multiplier: {sample_record.get('multiplier', 'N/A')}")
        
        return df, futures_df, spreads_df
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

def compare_approaches():
    """Compare parent symbology vs ALL_SYMBOLS approach"""
    print("\n" + "="*60)
    print("🆚 COMPARING APPROACHES: Parent Symbology vs ALL_SYMBOLS")
    print("="*60)
    
    client = db.Historical()
    dataset = "GLBX.MDP3"
    date = "2024-12-01"
    
    try:
        import time
        
        # Time parent symbology approach
        print("⏱️  Testing Parent Symbology (ES.FUT)...")
        start_time = time.time()
        parent_data = client.timeseries.get_range(
            dataset=dataset,
            symbols="ES.FUT",
            start=date,
            stype_in="parent",
            schema="definition",
        )
        parent_time = time.time() - start_time
        parent_df = parent_data.to_df()
        
        print(f"   📊 Parent symbology: {len(parent_df):,} records in {parent_time:.2f}s")
        
        # For comparison, let's see what ALL_SYMBOLS would return
        # (We'll limit this to avoid overwhelming the API)
        print("⏱️  Testing ALL_SYMBOLS approach (limited sample)...")
        start_time = time.time()
        all_data = client.timeseries.get_range(
            dataset=dataset,
            symbols="ALL_SYMBOLS",
            start=date,
            schema="definition",
        )
        all_time = time.time() - start_time
        all_df = all_data.to_df()
        
        # Filter for ES symbols
        es_all = all_df[all_df['raw_symbol'].str.startswith('ES')]
        
        print(f"   📊 ALL_SYMBOLS: {len(all_df):,} total, {len(es_all):,} ES symbols in {all_time:.2f}s")
        
        print(f"\n💡 EFFICIENCY COMPARISON:")
        print(f"   Parent symbology: {len(parent_df):,} ES instruments in {parent_time:.2f}s")
        print(f"   ALL_SYMBOLS filter: {len(es_all):,} ES instruments in {all_time:.2f}s")
        print(f"   Efficiency gain: {all_time/parent_time:.1f}x faster with parent symbology")
        print(f"   Data reduction: {len(all_df)/len(parent_df):.1f}x less data transferred")
        
    except Exception as e:
        print(f"❌ Comparison error: {e}")

if __name__ == "__main__":
    # Run main debug
    df, futures_df, spreads_df = debug_definition_schema()
    
    # Run comparison if main succeeded
    if df is not None:
        compare_approaches()
        
    print(f"\n✅ Debug complete! Use parent symbology for efficient ES futures data retrieval.") 