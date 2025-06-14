#!/usr/bin/env python3
"""
ES Futures Spread Analysis with Tick Size Normalization
Based on Databento's tick size handling example, adapted for ES futures
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

import databento as db
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def analyze_es_spread_with_ticks():
    """Analyze ES futures spread using definition schema for tick normalization"""
    print("🔍 ES FUTURES SPREAD ANALYSIS WITH TICK NORMALIZATION")
    print("="*70)
    
    # Use our discovered ES instrument IDs from the definition analysis
    # These are the standard quarterly ES contracts
    es_instruments = {
        'ESM5': 4916,    # June 2025
        'ESU5': 14160,   # September 2025  
        'ESZ5': 294973,  # December 2025
        'ESZ4': 183748,  # December 2024 (expired but for historical analysis)
    }
    
    # Define time range for analysis (recent trading session)
    dataset = "GLBX.MDP3"
    start = pd.Timestamp("2024-12-01T21:00:00", tz="US/Eastern")  # Sunday evening
    end = pd.Timestamp("2024-12-02T04:00:00", tz="US/Eastern")    # Monday morning
    
    client = db.Historical()
    print(f"✅ Connected to Databento API")
    print(f"📅 Analysis period: {start} to {end}")
    print(f"🎯 ES Contracts: {list(es_instruments.keys())}")
    
    # Method 1: Get definitions using instrument IDs (since symbol filtering is broken)
    print(f"\n📊 Retrieving ES definitions...")
    
    # Get definitions for our specific instrument IDs
    definitions_data = client.timeseries.get_range(
        dataset=dataset,
        schema="definition",
        start="2024-12-01",
        end="2024-12-02",
    )
    
    # Filter for our ES contracts and extract tick sizes
    definitions_df = definitions_data.to_df()
    
    # Filter for our specific ES instrument IDs
    es_definitions = definitions_df[
        definitions_df['instrument_id'].isin(es_instruments.values())
    ].copy()
    
    if es_definitions.empty:
        print("❌ No ES definitions found for our instrument IDs")
        print("🔄 Trying alternative approach with asset filtering...")
        
        # Alternative: Filter by asset = 'ES'
        es_definitions = definitions_df[
            definitions_df['asset'] == 'ES'
        ].copy()
    
    if es_definitions.empty:
        print("❌ No ES definitions found at all")
        return
    
    # Create tick size lookup
    tick_sizes = es_definitions[
        ['raw_symbol', 'instrument_id', 'min_price_increment']
    ].set_index('instrument_id')
    
    print(f"📋 Found {len(tick_sizes)} ES contracts with definitions:")
    for idx, row in tick_sizes.iterrows():
        print(f"   {row['raw_symbol']:>6} (ID: {idx:>6}) | Tick: ${row['min_price_increment']}")
    
    # Get the most liquid contracts (first few)
    target_instruments = tick_sizes.head(3).index.tolist()
    
    print(f"\n📈 Retrieving MBP-1 data for top 3 contracts...")
    print(f"   Target instrument IDs: {target_instruments}")
    
    # Get top-of-book data for our ES contracts
    # Note: We'll use instrument_id filtering if available, otherwise get all and filter
    try:
        mbp_data = client.timeseries.get_range(
            dataset=dataset,
            schema="mbp-1",
            start=start,
            end=end,
        )
        
        # Convert to DataFrame
        mbp_df = mbp_data.to_df(tz="US/Eastern")
        
        # Filter for our target ES instruments
        mbp_df = mbp_df[mbp_df['instrument_id'].isin(target_instruments)].copy()
        
        if mbp_df.empty:
            print("❌ No MBP data found for our ES instruments in the specified time range")
            print("💡 This might be because the time range is outside market hours")
            print("💡 or the instrument IDs are not active during this period")
            return
        
        print(f"✅ Retrieved {len(mbp_df):,} MBP records")
        
        # Join with tick size data
        mbp_df = mbp_df.join(tick_sizes, on='instrument_id')
        
        # Keep relevant columns
        mbp_df = mbp_df[['raw_symbol', 'ask_px_00', 'bid_px_00', 'min_price_increment']].copy()
        
        # Calculate spread in price units
        mbp_df['spread_price'] = mbp_df['ask_px_00'] - mbp_df['bid_px_00']
        
        # Calculate spread in number of ticks (normalized)
        mbp_df['spread_ticks'] = mbp_df['spread_price'] / mbp_df['min_price_increment']
        
        print(f"\n📊 SPREAD ANALYSIS RESULTS")
        print("="*50)
        
        # Summary statistics by contract
        for symbol, data in mbp_df.groupby('raw_symbol'):
            spread_stats = data['spread_ticks'].describe()
            tick_size = data['min_price_increment'].iloc[0]
            
            print(f"\n🎯 {symbol} (Tick Size: ${tick_size})")
            print(f"   Records: {len(data):,}")
            print(f"   Mean Spread: {spread_stats['mean']:.2f} ticks (${spread_stats['mean'] * tick_size:.4f})")
            print(f"   Median Spread: {spread_stats['50%']:.2f} ticks")
            print(f"   Min Spread: {spread_stats['min']:.2f} ticks")
            print(f"   Max Spread: {spread_stats['max']:.2f} ticks")
            print(f"   Std Dev: {spread_stats['std']:.2f} ticks")
        
        # Create visualization
        print(f"\n📈 Creating spread visualization...")
        
        plt.figure(figsize=(12, 8))
        
        # Plot mean spread for each contract
        for symbol, data in mbp_df.groupby('raw_symbol'):
            if len(data) > 10:  # Only plot if we have sufficient data
                # Calculate rolling mean spread (5-minute window)
                mean_spread = (
                    data['spread_ticks']
                    .ewm(
                        times=data.index,
                        halflife=pd.Timedelta(minutes=5),
                    )
                    .mean()
                    .reset_index()
                )
                
                plt.plot(
                    'ts_recv',
                    'spread_ticks',
                    data=mean_spread,
                    label=f'{symbol} (n={len(data):,})',
                    linewidth=2,
                )
        
        plt.legend()
        plt.title(f'ES Futures Mean Spread Analysis - {start.date()}')
        plt.ylabel('Mean Spread (ticks)')
        plt.xlabel('Time (EST)')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save plot
        plot_path = os.path.join(os.path.dirname(__file__), 'es_spread_analysis.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        print(f"📁 Plot saved to: {plot_path}")
        
        # Show plot
        plt.show()
        
        # Export detailed data to CSV
        csv_path = os.path.join(os.path.dirname(__file__), 'es_spread_data.csv')
        mbp_df.to_csv(csv_path)
        print(f"📁 Detailed data exported to: {csv_path}")
        
    except Exception as e:
        print(f"❌ Error retrieving MBP data: {e}")
        print("💡 This might be due to:")
        print("   - Time range outside of available data")
        print("   - Instrument IDs not active during the period")
        print("   - Market hours restrictions")
        
        # Show what we found in definitions anyway
        print(f"\n📋 Available ES definitions found:")
        print(tick_sizes.to_string())
    
    print(f"\n🎯 KEY INSIGHTS:")
    print("-" * 50)
    print(f"✅ Definition schema provides essential tick size data")
    print(f"✅ Standard ES futures typically have $0.25 tick size")
    print(f"✅ Micro variants (ESR, etc.) have smaller tick sizes")
    print(f"✅ Spread normalization enables cross-contract comparison")
    print(f"✅ Tick-normalized spreads reveal true liquidity differences")
    
    print(f"\n💡 PRACTICAL APPLICATIONS:")
    print("-" * 50)
    print(f"🔹 Risk Management: Normalize position sizes by tick value")
    print(f"🔹 Execution Analysis: Compare transaction costs across contracts")
    print(f"🔹 Liquidity Assessment: Identify most liquid contract months")
    print(f"🔹 Arbitrage Detection: Spot spread anomalies between related contracts")

if __name__ == "__main__":
    try:
        analyze_es_spread_with_ticks()
    except ImportError as e:
        if 'matplotlib' in str(e):
            print("❌ matplotlib not installed. Install with: pip install matplotlib")
        else:
            print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc() 