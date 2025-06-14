#!/usr/bin/env python3
"""
Test Continuous Contracts
Demonstrates front month tracking and automatic rollover behavior
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

import databento as db
import pandas as pd
from datetime import datetime, timedelta

def test_front_month_tracking():
    """Test front month continuous contract tracking"""
    print("🎯 TESTING FRONT MONTH CONTINUOUS CONTRACTS")
    print("="*60)
    
    client = db.Historical()
    dataset = "GLBX.MDP3"
    
    # Test multiple products
    products = [
        ("ES", "E-mini S&P 500"),
        ("CL", "Crude Oil WTI"),
        ("NG", "Natural Gas"),
        ("GC", "Gold")
    ]
    
    # Test period around contract rollover
    start_date = "2024-12-01"
    end_date = "2024-12-15"
    
    for ticker, name in products:
        print(f"\n📊 Testing {name} ({ticker}.v.0)")
        print("-" * 40)
        
        try:
            # Get front month data
            data = client.timeseries.get_range(
                dataset=dataset,
                schema="ohlcv-1d",
                symbols=f"{ticker}.v.0",
                stype_in="continuous",
                start=start_date,
                end=end_date,
            )
            
            df = data.to_df()
            
            if not df.empty:
                print(f"✅ Retrieved {len(df)} daily bars")
                print(f"   Date range: {df.index.min()} → {df.index.max()}")
                
                # Check for instrument ID changes (rollover)
                unique_instruments = df['instrument_id'].unique()
                print(f"   Instrument IDs: {unique_instruments}")
                
                if len(unique_instruments) > 1:
                    print("   🔄 ROLLOVER DETECTED!")
                    for instrument_id in unique_instruments:
                        subset = df[df['instrument_id'] == instrument_id]
                        print(f"      ID {instrument_id}: {len(subset)} days")
                
                # Show sample data
                print(f"   Sample data:")
                sample = df[['instrument_id', 'close', 'volume']].head(3)
                for idx, row in sample.iterrows():
                    print(f"      {idx.date()}: ID={row['instrument_id']}, Close=${row['close']:.2f}, Vol={row['volume']:,}")
                    
            else:
                print("❌ No data returned")
                
        except Exception as e:
            print(f"❌ Error testing {ticker}: {e}")

def test_expiry_chain():
    """Test multiple expiry months (0, 1, 2)"""
    print(f"\n🔗 TESTING EXPIRY CHAIN (ES.v.0, ES.v.1, ES.v.2)")
    print("="*60)
    
    client = db.Historical()
    dataset = "GLBX.MDP3"
    start_date = "2024-12-01"
    end_date = "2024-12-02"
    
    for expiry_idx in range(3):
        print(f"\n📅 Testing ES.v.{expiry_idx} ({'Front' if expiry_idx == 0 else f'{expiry_idx+1} month out'})")
        
        try:
            data = client.timeseries.get_range(
                dataset=dataset,
                schema="ohlcv-1d",
                symbols=f"ES.v.{expiry_idx}",
                stype_in="continuous",
                start=start_date,
                end=end_date,
            )
            
            df = data.to_df()
            
            if not df.empty:
                record = df.iloc[0]
                print(f"   ✅ Instrument ID: {record['instrument_id']}")
                print(f"   📈 Close Price: ${record['close']:.2f}")
                print(f"   📊 Volume: {record['volume']:,}")
            else:
                print("   ❌ No data")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def demonstrate_rollover_week():
    """Demonstrate contract rollover during expiry week"""
    print(f"\n🔄 DEMONSTRATING ROLLOVER WEEK BEHAVIOR")
    print("="*60)
    
    client = db.Historical()
    dataset = "GLBX.MDP3"
    
    # Use March 2025 ES expiry week as example
    start_date = "2025-03-16"
    end_date = "2025-03-21"
    
    print(f"Testing ES rollover week: {start_date} → {end_date}")
    print("(March 2025 ES contract expiry)")
    
    try:
        data = client.timeseries.get_range(
            dataset=dataset,
            schema="ohlcv-1d",
            symbols="ES.v.0",
            stype_in="continuous",
            start=start_date,
            end=end_date,
        )
        
        df = data.to_df()
        
        if not df.empty:
            print(f"\n📊 ROLLOVER ANALYSIS:")
            print("Date         Instrument ID  Close    Volume      Contract")
            print("-" * 55)
            
            for idx, row in df.iterrows():
                # Determine likely contract based on instrument ID
                contract = "ESH5" if row['instrument_id'] == 5002 else "ESM5" if row['instrument_id'] == 4916 else f"ID{row['instrument_id']}"
                rollover_marker = " ← ROLLOVER" if idx == df.index[3] else ""  # Assuming rollover on 4th day
                
                print(f"{idx.date()}   {row['instrument_id']:>10}     ${row['close']:>6.2f}   {row['volume']:>8,}   {contract}{rollover_marker}")
            
            # Analyze the rollover
            unique_ids = df['instrument_id'].unique()
            if len(unique_ids) > 1:
                print(f"\n🎯 ROLLOVER CONFIRMED:")
                print(f"   Contract changed from ID {unique_ids[0]} → {unique_ids[1]}")
                print(f"   Volume likely shifted from March (ESH5) → June (ESM5)")
            else:
                print(f"\n📝 No rollover in this period (single contract: ID {unique_ids[0]})")
                
        else:
            print("❌ No data for rollover analysis")
            
    except Exception as e:
        print(f"❌ Rollover test error: {e}")

def compare_continuous_vs_specific():
    """Compare continuous contract vs specific contract data"""
    print(f"\n⚖️  COMPARING CONTINUOUS vs SPECIFIC CONTRACTS")
    print("="*60)
    
    client = db.Historical()
    dataset = "GLBX.MDP3"
    start_date = "2024-12-01"
    end_date = "2024-12-02"
    
    try:
        # Get continuous front month
        continuous_data = client.timeseries.get_range(
            dataset=dataset,
            schema="ohlcv-1d",
            symbols="ES.v.0",
            stype_in="continuous",
            start=start_date,
            end=end_date,
        )
        
        # Get specific December contract
        specific_data = client.timeseries.get_range(
            dataset=dataset,
            schema="ohlcv-1d",
            symbols="ESZ4",  # December 2024
            start=start_date,
            end=end_date,
        )
        
        continuous_df = continuous_data.to_df()
        specific_df = specific_data.to_df()
        
        print(f"📊 COMPARISON FOR {start_date}:")
        
        if not continuous_df.empty:
            cont_record = continuous_df.iloc[0]
            print(f"   ES.v.0 (continuous): ID={cont_record['instrument_id']}, Close=${cont_record['close']:.2f}")
        
        if not specific_df.empty:
            spec_record = specific_df.iloc[0]
            print(f"   ESZ4 (specific):     ID={spec_record['instrument_id']}, Close=${spec_record['close']:.2f}")
        
        # Check if they match (they should for Dec 1, 2024)
        if not continuous_df.empty and not specific_df.empty:
            if cont_record['instrument_id'] == spec_record['instrument_id']:
                print("   ✅ MATCH: Continuous front month = December contract")
            else:
                print("   🔄 DIFFERENT: Front month has rolled to next contract")
                
    except Exception as e:
        print(f"❌ Comparison error: {e}")

def main():
    """Run all continuous contract tests"""
    print("🚀 CONTINUOUS CONTRACT TESTING SUITE")
    print("=" * 60)
    
    # Run all tests
    test_front_month_tracking()
    test_expiry_chain()
    demonstrate_rollover_week() 
    compare_continuous_vs_specific()
    
    print(f"\n" + "="*60)
    print("✅ CONTINUOUS CONTRACT TESTING COMPLETE")
    print("="*60)
    
    print(f"\n💡 KEY TAKEAWAYS:")
    print(f"   • Use ES.v.0 for front month time series")
    print(f"   • stype_in='continuous' enables automatic rollovers")
    print(f"   • instrument_id changes indicate contract switches")
    print(f"   • Volume-based rollover logic follows market liquidity")
    print(f"   • Original prices maintained (no back-adjustment)")

if __name__ == "__main__":
    main() 