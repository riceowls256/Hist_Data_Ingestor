#!/usr/bin/env python3
"""
ES Futures Liquidity Analysis
Find the most liquid ES futures contracts using statistics, definition, and BBO data
Based on Databento's liquid instruments example, adapted for ES futures
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

import databento as db
import pandas as pd
from datetime import datetime, timedelta

def analyze_es_liquidity():
    """Analyze ES futures liquidity using volume, open interest, and spread metrics"""
    print("🔍 ES FUTURES LIQUIDITY ANALYSIS")
    print("="*60)
    
    # Use our discovered ES instrument IDs
    known_es_instruments = [4916, 14160, 294973, 183748]  # ESM5, ESU5, ESZ5, ESZ4
    
    client = db.Historical()
    dataset = "GLBX.MDP3"
    start_date = "2024-12-01"
    
    print(f"✅ Connected to Databento API")
    print(f"📅 Analysis date: {start_date}")
    print(f"🎯 Target: ES futures liquidity analysis")
    
    # Step 1: Get definition data for all symbols (since symbol filtering is broken)
    print(f"\n📊 Step 1: Retrieving definition data...")
    
    try:
        def_data = client.timeseries.get_range(
            dataset=dataset,
            schema="definition",
            start=start_date,
        )
        
        # Convert to DataFrame and filter for futures
        def_df = def_data.to_df()
        print(f"   Retrieved {len(def_df):,} definition records")
        
        # Filter for futures only
        futures_df = def_df[def_df["instrument_class"] == db.InstrumentClass.FUTURE].copy()
        print(f"   Filtered to {len(futures_df):,} futures contracts")
        
        # Filter for ES-related contracts
        es_def_df = futures_df[
            (futures_df["asset"].str.startswith("ES", na=False)) |
            (futures_df["raw_symbol"].str.startswith("ES", na=False))
        ].copy()
        
        print(f"   Found {len(es_def_df)} ES-related contracts")
        
        # Keep relevant columns
        es_def_df = es_def_df[["raw_symbol", "instrument_id", "asset", "min_price_increment", "security_type"]].copy()
        
        if es_def_df.empty:
            print("❌ No ES contracts found in definition data")
            return
        
        print(f"📋 ES Contracts Found:")
        for _, row in es_def_df.head(10).iterrows():
            print(f"   {row['raw_symbol']:>10} | ID: {row['instrument_id']:>8} | Asset: {row['asset']:>4} | Tick: ${row['min_price_increment']}")
        
    except Exception as e:
        print(f"❌ Error retrieving definition data: {e}")
        return
    
    # Step 2: Get statistics data for volume and open interest
    print(f"\n📈 Step 2: Retrieving statistics data...")
    
    try:
        stats_data = client.timeseries.get_range(
            dataset=dataset,
            schema="statistics",
            start=start_date,
        )
        
        # Convert to DataFrame
        stats_df = stats_data.to_df()
        print(f"   Retrieved {len(stats_df):,} statistics records")
        
        # Filter for our ES instruments
        es_instrument_ids = es_def_df["instrument_id"].tolist()
        es_stats_df = stats_df[stats_df["instrument_id"].isin(es_instrument_ids)].copy()
        
        print(f"   Found {len(es_stats_df)} statistics records for ES contracts")
        
        if es_stats_df.empty:
            print("❌ No statistics data found for ES contracts")
            print("💡 This might be because:")
            print("   - Date is outside available statistics data")
            print("   - ES contracts not active on this date")
            print("   - Statistics schema has different coverage")
            
            # Show what we found in definitions
            print(f"\n📋 Available ES definitions (using for analysis):")
            print(es_def_df.to_string(index=False))
            
            # Create mock statistics for demonstration
            print(f"\n🔄 Creating mock statistics for demonstration...")
            mock_stats = []
            for _, contract in es_def_df.head(10).iterrows():
                # Simulate volume and open interest based on contract type
                if contract['asset'] == 'ES':
                    volume = 50000 + (hash(str(contract['instrument_id'])) % 100000)
                    open_interest = 100000 + (hash(str(contract['instrument_id'])) % 200000)
                else:
                    volume = 10000 + (hash(str(contract['instrument_id'])) % 50000)
                    open_interest = 20000 + (hash(str(contract['instrument_id'])) % 100000)
                
                mock_stats.append({
                    'instrument_id': contract['instrument_id'],
                    'volume': volume,
                    'open_interest': open_interest
                })
            
            mock_stats_df = pd.DataFrame(mock_stats)
            
        else:
            # Process real statistics data
            # Get cleared volume records
            volume_df = es_stats_df[es_stats_df["stat_type"] == db.StatType.CLEARED_VOLUME].copy()
            volume_df = volume_df.drop_duplicates("instrument_id", keep="last")
            volume_df = volume_df.rename(columns={"quantity": "volume"})
            volume_df = volume_df[["instrument_id", "volume"]]
            
            # Get open interest records
            open_interest_df = es_stats_df[es_stats_df["stat_type"] == db.StatType.OPEN_INTEREST].copy()
            open_interest_df = open_interest_df.drop_duplicates("instrument_id", keep="last")
            open_interest_df = open_interest_df.rename(columns={"quantity": "open_interest"})
            open_interest_df = open_interest_df[["instrument_id", "open_interest"]]
            
            # Merge volume and open interest data
            mock_stats_df = volume_df.merge(open_interest_df, on="instrument_id", how="outer").fillna(0)
        
        # Merge definition data with statistics data
        liquidity_df = mock_stats_df.merge(es_def_df, on="instrument_id", how="inner")
        
        print(f"✅ Merged data for {len(liquidity_df)} ES contracts")
        
    except Exception as e:
        print(f"❌ Error retrieving statistics data: {e}")
        print("🔄 Proceeding with definition data only...")
        
        # Create basic liquidity analysis with just definitions
        liquidity_df = es_def_df.copy()
        liquidity_df['volume'] = 0
        liquidity_df['open_interest'] = 0
    
    # Step 3: Analyze liquidity patterns
    print(f"\n📊 Step 3: Analyzing liquidity patterns...")
    
    # Sort by volume and group by asset type
    liquidity_df = liquidity_df.sort_values("volume", ascending=False)
    
    print(f"\n🏆 TOP ES CONTRACTS BY VOLUME:")
    print("-" * 80)
    print(f"{'Rank':>4} | {'Symbol':>10} | {'Asset':>6} | {'Volume':>10} | {'Open Int':>10} | {'Tick Size':>10}")
    print("-" * 80)
    
    for i, (_, row) in enumerate(liquidity_df.head(15).iterrows(), 1):
        print(f"{i:>4} | {row['raw_symbol']:>10} | {row['asset']:>6} | "
              f"{row['volume']:>10,} | {row['open_interest']:>10,} | ${row['min_price_increment']:>9.4f}")
    
    # Group by asset type for comparison
    print(f"\n📈 LIQUIDITY BY ASSET TYPE:")
    print("-" * 60)
    
    asset_summary = liquidity_df.groupby('asset').agg({
        'volume': ['count', 'sum', 'mean'],
        'open_interest': ['sum', 'mean'],
        'min_price_increment': ['min', 'max', 'mean']
    }).round(4)
    
    for asset in asset_summary.index:
        count = int(asset_summary.loc[asset, ('volume', 'count')])
        total_vol = int(asset_summary.loc[asset, ('volume', 'sum')])
        avg_vol = int(asset_summary.loc[asset, ('volume', 'mean')])
        total_oi = int(asset_summary.loc[asset, ('open_interest', 'sum')])
        avg_tick = asset_summary.loc[asset, ('min_price_increment', 'mean')]
        
        print(f"{asset:>6}: {count:>2} contracts | Vol: {total_vol:>10,} (avg: {avg_vol:>8,}) | "
              f"OI: {total_oi:>10,} | Avg Tick: ${avg_tick:>6.4f}")
    
    # Step 4: Get BBO data for top contracts (if available)
    print(f"\n📊 Step 4: Analyzing bid-ask spreads...")
    
    # Get top 10 most liquid contracts
    top_contracts = liquidity_df.head(10)["instrument_id"].tolist()
    
    try:
        print(f"   Attempting to retrieve BBO data for top {len(top_contracts)} contracts...")
        
        # Try to get BBO data
        bbo_data = client.timeseries.get_range(
            dataset=dataset,
            symbols=top_contracts,
            stype_in="instrument_id",
            schema="bbo-1s",
            start=start_date,
        )
        
        # Convert to DataFrame
        bbo_df = bbo_data.to_df()
        
        if not bbo_df.empty:
            print(f"   Retrieved {len(bbo_df):,} BBO records")
            
            # Merge with liquidity data
            spread_df = bbo_df.merge(liquidity_df, on="instrument_id", how="inner")
            spread_df["spread_ticks"] = (spread_df["ask_px_00"] - spread_df["bid_px_00"]) / spread_df["min_price_increment"]
            
            # Calculate aggregated spread metrics
            spread_summary = (
                spread_df.groupby("instrument_id")
                .agg(
                    symbol=("raw_symbol", "first"),
                    asset=("asset", "first"),
                    volume=("volume", "first"),
                    open_interest=("open_interest", "first"),
                    median_bid_size=("bid_sz_00", lambda x: int(x.median()) if len(x) > 0 else 0),
                    median_ask_size=("ask_sz_00", lambda x: int(x.median()) if len(x) > 0 else 0),
                    median_tick_spread=("spread_ticks", lambda x: round(x.median(), 2) if len(x) > 0 else 0),
                    avg_tick_spread=("spread_ticks", lambda x: round(x.mean(), 2) if len(x) > 0 else 0),
                )
                .sort_values("volume", ascending=False)
            )
            
            print(f"\n💰 SPREAD ANALYSIS RESULTS:")
            print("-" * 100)
            print(f"{'Symbol':>10} | {'Asset':>6} | {'Volume':>10} | {'Med Spread':>10} | {'Avg Spread':>10} | {'Bid Size':>8} | {'Ask Size':>8}")
            print("-" * 100)
            
            for _, row in spread_summary.iterrows():
                print(f"{row['symbol']:>10} | {row['asset']:>6} | {row['volume']:>10,} | "
                      f"{row['median_tick_spread']:>9.2f}t | {row['avg_tick_spread']:>9.2f}t | "
                      f"{row['median_bid_size']:>8} | {row['median_ask_size']:>8}")
            
        else:
            print("❌ No BBO data found for the specified date/contracts")
            
    except Exception as e:
        print(f"❌ Error retrieving BBO data: {e}")
        print("💡 This might be due to:")
        print("   - Date outside available BBO data")
        print("   - Contracts not active during this period")
        print("   - Weekend/holiday with no trading")
    
    # Step 5: Liquidity scoring and recommendations
    print(f"\n🎯 LIQUIDITY SCORING & RECOMMENDATIONS:")
    print("-" * 60)
    
    # Create liquidity score based on available data
    liquidity_df['liquidity_score'] = 0
    
    # Volume component (40% weight)
    if liquidity_df['volume'].max() > 0:
        liquidity_df['volume_score'] = (liquidity_df['volume'] / liquidity_df['volume'].max()) * 40
        liquidity_df['liquidity_score'] += liquidity_df['volume_score']
    
    # Open interest component (30% weight)
    if liquidity_df['open_interest'].max() > 0:
        liquidity_df['oi_score'] = (liquidity_df['open_interest'] / liquidity_df['open_interest'].max()) * 30
        liquidity_df['liquidity_score'] += liquidity_df['oi_score']
    
    # Tick size component (30% weight - smaller tick = more liquid)
    if liquidity_df['min_price_increment'].max() > 0:
        # Invert tick size (smaller = better)
        max_tick = liquidity_df['min_price_increment'].max()
        liquidity_df['tick_score'] = ((max_tick - liquidity_df['min_price_increment']) / max_tick) * 30
        liquidity_df['liquidity_score'] += liquidity_df['tick_score']
    
    # Sort by liquidity score
    liquidity_ranked = liquidity_df.sort_values('liquidity_score', ascending=False)
    
    print(f"{'Rank':>4} | {'Symbol':>10} | {'Asset':>6} | {'Score':>6} | {'Recommendation':>15}")
    print("-" * 60)
    
    for i, (_, row) in enumerate(liquidity_ranked.head(10).iterrows(), 1):
        score = row['liquidity_score']
        if score >= 70:
            recommendation = "Highly Liquid"
        elif score >= 50:
            recommendation = "Moderately Liquid"
        elif score >= 30:
            recommendation = "Low Liquidity"
        else:
            recommendation = "Illiquid"
        
        print(f"{i:>4} | {row['raw_symbol']:>10} | {row['asset']:>6} | {score:>6.1f} | {recommendation:>15}")
    
    # Export results
    csv_path = os.path.join(os.path.dirname(__file__), "es_liquidity_analysis.csv")
    liquidity_ranked.to_csv(csv_path, index=False)
    print(f"\n📁 Results exported to: {csv_path}")
    
    print(f"\n🎯 KEY INSIGHTS:")
    print("-" * 50)
    print(f"✅ Standard ES futures (asset='ES') typically most liquid")
    print(f"✅ Front month contracts usually have highest volume")
    print(f"✅ Micro variants (ESR) offer fine-grained position sizing")
    print(f"✅ Spread contracts useful for relative value trading")
    print(f"✅ Consider both volume AND open interest for liquidity assessment")
    
    print(f"\n💡 TRADING RECOMMENDATIONS:")
    print("-" * 50)
    print(f"🔹 Use top-ranked contracts for active trading strategies")
    print(f"🔹 Monitor spread patterns to assess market conditions")
    print(f"🔹 Consider contract rollover dates for position management")
    print(f"🔹 Use micro contracts (ESR) for precise risk management")
    print(f"🔹 Avoid illiquid contracts for large position sizes")

if __name__ == "__main__":
    analyze_es_liquidity() 