#!/usr/bin/env python3
"""
Complete Workflow Demonstration
Shows the full process: Symbol Discovery → Filtering → Liquidity Analysis → Trading Recommendations
Demonstrates best practices learned from our comprehensive analysis
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

import databento as db
import pandas as pd
from datetime import datetime, timedelta

def complete_workflow_demo():
    """Demonstrate complete workflow from symbol discovery to trading recommendations"""
    print("🚀 COMPLETE DATABENTO WORKFLOW DEMONSTRATION")
    print("="*70)
    
    client = db.Historical()
    dataset = "GLBX.MDP3"
    analysis_date = "2024-12-01"
    
    print(f"📊 Dataset: {dataset}")
    print(f"📅 Analysis Date: {analysis_date}")
    
    # Step 1: Symbol Discovery
    print(f"\n🔍 STEP 1: SYMBOL DISCOVERY")
    print("-" * 50)
    
    try:
        print(f"   Retrieving complete symbol universe...")
        
        # Get all symbols using definition schema
        data = client.timeseries.get_range(
            dataset=dataset,
            symbols="ALL_SYMBOLS",
            start=analysis_date,
            schema="definition",
        )
        
        # Create symbol map
        symbol_map = {msg.raw_symbol: msg for msg in data}
        all_symbols = sorted(symbol_map.keys())
        
        print(f"   ✅ Retrieved {len(all_symbols):,} symbols")
        
    except Exception as e:
        print(f"   ❌ Error in symbol discovery: {e}")
        return
    
    # Step 2: Intelligent Filtering
    print(f"\n🎯 STEP 2: INTELLIGENT FILTERING")
    print("-" * 50)
    
    # Filter for ES futures (our target)
    es_futures = []
    for symbol, msg in symbol_map.items():
        if (hasattr(msg, 'instrument_class') and 
            str(msg.instrument_class) == 'InstrumentClass.FUTURE' and
            hasattr(msg, 'asset') and 
            msg.asset == 'ES'):
            es_futures.append({
                'symbol': symbol,
                'instrument_id': msg.instrument_id,
                'asset': msg.asset,
                'tick_size': msg.min_price_increment,
                'expiration': msg.expiration
            })
    
    print(f"   📊 Filtered to {len(es_futures)} ES futures contracts")
    
    if not es_futures:
        print(f"   ❌ No ES futures found")
        return
    
    # Convert to DataFrame for analysis
    es_df = pd.DataFrame(es_futures)
    
    # Show sample
    print(f"   📋 Sample ES futures:")
    for i, contract in enumerate(es_df.head(5).to_dict('records')):
        print(f"      {i+1}. {contract['symbol']} (ID: {contract['instrument_id']})")
    
    # Step 3: Liquidity Analysis
    print(f"\n📈 STEP 3: LIQUIDITY ANALYSIS")
    print("-" * 50)
    
    # Get instrument IDs for statistics lookup
    target_instrument_ids = es_df['instrument_id'].tolist()[:10]  # Limit for demo
    
    try:
        print(f"   Analyzing liquidity for top {len(target_instrument_ids)} contracts...")
        
        # Get statistics data
        stats_data = client.timeseries.get_range(
            dataset=dataset,
            schema="statistics",
            start=analysis_date,
        )
        
        stats_df = stats_data.to_df()
        
        # Filter for our target instruments
        target_stats = stats_df[stats_df["instrument_id"].isin(target_instrument_ids)]
        
        if target_stats.empty:
            print(f"   ⚠️  No statistics data found, creating simulated data for demo...")
            
            # Create simulated liquidity data
            liquidity_data = []
            for _, contract in es_df.head(10).iterrows():
                # Simulate realistic volume based on contract characteristics
                base_volume = 100000
                volume_variation = hash(str(contract['instrument_id'])) % 500000
                simulated_volume = base_volume + volume_variation
                
                base_oi = 200000
                oi_variation = hash(str(contract['instrument_id'])) % 1000000
                simulated_oi = base_oi + oi_variation
                
                liquidity_data.append({
                    'symbol': contract['symbol'],
                    'instrument_id': contract['instrument_id'],
                    'volume': simulated_volume,
                    'open_interest': simulated_oi,
                    'tick_size': contract['tick_size']
                })
            
            liquidity_df = pd.DataFrame(liquidity_data)
            
        else:
            print(f"   ✅ Found {len(target_stats)} statistics records")
            
            # Process real statistics data
            volume_df = target_stats[target_stats["stat_type"] == db.StatType.CLEARED_VOLUME]
            volume_df = volume_df.drop_duplicates("instrument_id", keep="last")
            volume_df = volume_df.rename(columns={"quantity": "volume"})
            
            oi_df = target_stats[target_stats["stat_type"] == db.StatType.OPEN_INTEREST]
            oi_df = oi_df.drop_duplicates("instrument_id", keep="last")
            oi_df = oi_df.rename(columns={"quantity": "open_interest"})
            
            # Merge with contract data
            stats_merged = volume_df.merge(oi_df, on="instrument_id", how="outer").fillna(0)
            liquidity_df = stats_merged.merge(
                es_df[['symbol', 'instrument_id', 'tick_size']], 
                on="instrument_id", 
                how="inner"
            )
        
        print(f"   ✅ Prepared liquidity data for {len(liquidity_df)} contracts")
        
    except Exception as e:
        print(f"   ❌ Error in liquidity analysis: {e}")
        return
    
    # Step 4: Liquidity Scoring
    print(f"\n🏆 STEP 4: LIQUIDITY SCORING")
    print("-" * 50)
    
    # Calculate liquidity scores
    liquidity_df['liquidity_score'] = 0
    
    # Volume component (60% weight)
    if liquidity_df['volume'].max() > 0:
        liquidity_df['volume_score'] = (liquidity_df['volume'] / liquidity_df['volume'].max()) * 60
        liquidity_df['liquidity_score'] += liquidity_df['volume_score']
    
    # Open interest component (40% weight)
    if liquidity_df['open_interest'].max() > 0:
        liquidity_df['oi_score'] = (liquidity_df['open_interest'] / liquidity_df['open_interest'].max()) * 40
        liquidity_df['liquidity_score'] += liquidity_df['oi_score']
    
    # Sort by liquidity score
    liquidity_ranked = liquidity_df.sort_values('liquidity_score', ascending=False)
    
    print(f"   📊 LIQUIDITY RANKINGS:")
    print(f"   {'Rank':>4} | {'Symbol':>10} | {'Volume':>12} | {'Open Int':>12} | {'Score':>6}")
    print(f"   {'-'*60}")
    
    for i, (_, row) in enumerate(liquidity_ranked.head(8).iterrows(), 1):
        print(f"   {i:>4} | {row['symbol']:>10} | {row['volume']:>12,} | "
              f"{row['open_interest']:>12,} | {row['liquidity_score']:>6.1f}")
    
    # Step 5: Trading Recommendations
    print(f"\n💡 STEP 5: TRADING RECOMMENDATIONS")
    print("-" * 50)
    
    top_contracts = liquidity_ranked.head(3)
    
    print(f"   🎯 TOP 3 RECOMMENDED CONTRACTS:")
    for i, (_, contract) in enumerate(top_contracts.iterrows(), 1):
        tick_value = 12.50  # Standard ES tick value
        spread_cost = 1.0 * tick_value  # Assume 1-tick spread
        
        print(f"\n   {i}. {contract['symbol']}")
        print(f"      💰 Liquidity Score: {contract['liquidity_score']:.1f}/100")
        print(f"      📊 Daily Volume: {contract['volume']:,}")
        print(f"      🏦 Open Interest: {contract['open_interest']:,}")
        print(f"      💸 Est. Spread Cost: ${spread_cost:.2f} per contract")
        
        # Trading recommendations based on score
        if contract['liquidity_score'] >= 80:
            recommendation = "Excellent for high-frequency strategies"
        elif contract['liquidity_score'] >= 60:
            recommendation = "Good for active trading"
        elif contract['liquidity_score'] >= 40:
            recommendation = "Suitable for position trading"
        else:
            recommendation = "Use with caution - lower liquidity"
        
        print(f"      🎯 Recommendation: {recommendation}")
    
    # Step 6: Risk Management Insights
    print(f"\n⚠️  STEP 6: RISK MANAGEMENT INSIGHTS")
    print("-" * 50)
    
    print(f"   📏 POSITION SIZING GUIDELINES:")
    print(f"   • Standard ES tick value: $12.50")
    print(f"   • 1-point move = 4 ticks = $50.00")
    print(f"   • Daily range typically 20-50 points ($1,000-$2,500)")
    
    print(f"\n   🎯 STRATEGY RECOMMENDATIONS:")
    print(f"   • Use top-ranked contracts for scalping strategies")
    print(f"   • Monitor volume patterns for optimal entry/exit")
    print(f"   • Consider contract rollover dates (quarterly)")
    print(f"   • Implement proper risk controls based on tick values")
    
    # Step 7: Export Results
    print(f"\n📁 STEP 7: EXPORT RESULTS")
    print("-" * 50)
    
    # Export workflow results
    workflow_results = liquidity_ranked.copy()
    workflow_results['analysis_date'] = analysis_date
    workflow_results['dataset'] = dataset
    workflow_results['tick_value_usd'] = 12.50
    
    export_path = os.path.join(os.path.dirname(__file__), "workflow_results.csv")
    workflow_results.to_csv(export_path, index=False)
    
    print(f"   ✅ Results exported to: workflow_results.csv")
    print(f"   📊 Contains {len(workflow_results)} analyzed contracts")
    
    # Summary statistics
    print(f"\n📈 WORKFLOW SUMMARY")
    print("-" * 50)
    print(f"   🔍 Total symbols discovered: {len(all_symbols):,}")
    print(f"   🎯 ES futures identified: {len(es_futures)}")
    print(f"   📊 Contracts analyzed: {len(liquidity_df)}")
    print(f"   🏆 Top recommendation: {top_contracts.iloc[0]['symbol']}")
    print(f"   ⏱️  Analysis completed successfully")
    
    print(f"\n🎯 KEY TAKEAWAYS:")
    print("-" * 50)
    print(f"   ✅ Symbol discovery provides complete market view")
    print(f"   ✅ Intelligent filtering focuses on relevant instruments")
    print(f"   ✅ Multi-factor liquidity analysis enables optimal selection")
    print(f"   ✅ Risk-aware recommendations support trading decisions")
    print(f"   ✅ Scalable workflow applicable to any asset class")

def main():
    """Main execution function"""
    print("🌟 DATABENTO COMPLETE WORKFLOW DEMO")
    print("="*70)
    print("This demo shows the complete process from symbol discovery")
    print("to trading recommendations using Databento's API.")
    print()
    
    complete_workflow_demo()
    
    print(f"\n🚀 NEXT STEPS:")
    print("-" * 30)
    print(f"1. Adapt this workflow for your target asset class")
    print(f"2. Integrate with your trading infrastructure")
    print(f"3. Add real-time data feeds for live trading")
    print(f"4. Implement proper risk management controls")
    print(f"5. Monitor and optimize based on performance")

if __name__ == "__main__":
    main() 