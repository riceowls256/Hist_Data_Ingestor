#!/usr/bin/env python3
"""
Tick Size Demonstration using Definition Schema
Shows how to use definition data for practical tick calculations
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

import databento as db
import pandas as pd

def demonstrate_tick_calculations():
    """Demonstrate practical tick size calculations using definition data"""
    print("🔍 TICK SIZE CALCULATION DEMONSTRATION")
    print("="*60)
    
    # Load our previously saved ES contracts data
    csv_path = os.path.join(os.path.dirname(__file__), "es_futures_contracts.csv")
    
    if not os.path.exists(csv_path):
        print("❌ ES futures CSV not found. Run the definition analysis first.")
        return
    
    # Load ES contracts data
    es_contracts = pd.read_csv(csv_path)
    print(f"📊 Loaded {len(es_contracts)} ES contracts from previous analysis")
    
    # Focus on standard ES futures (asset = 'ES')
    standard_es = es_contracts[es_contracts['asset'] == 'ES'].copy()
    
    print(f"\n📋 STANDARD ES FUTURES TICK SIZES:")
    print("-" * 50)
    
    for _, contract in standard_es.head(10).iterrows():
        symbol = contract['raw_symbol']
        tick_size = float(contract['tick_size'])
        instrument_id = contract['instrument_id']
        
        print(f"   {symbol:>8} (ID: {instrument_id:>6}) | Tick: ${tick_size:>6.2f}")
    
    # Demonstrate tick calculations
    print(f"\n💰 TICK VALUE CALCULATIONS:")
    print("-" * 50)
    
    # Example prices and spreads
    example_data = [
        {'symbol': 'ESM5', 'bid': 5850.25, 'ask': 5850.50, 'tick_size': 0.25},
        {'symbol': 'ESU5', 'bid': 5845.75, 'ask': 5846.25, 'tick_size': 0.25},
        {'symbol': 'ESZ5', 'bid': 5840.00, 'ask': 5840.75, 'tick_size': 0.25},
    ]
    
    print(f"{'Symbol':>8} | {'Bid':>8} | {'Ask':>8} | {'Spread $':>9} | {'Spread Ticks':>12} | {'Tick Size':>10}")
    print("-" * 70)
    
    for data in example_data:
        spread_price = data['ask'] - data['bid']
        spread_ticks = spread_price / data['tick_size']
        
        print(f"{data['symbol']:>8} | {data['bid']:>8.2f} | {data['ask']:>8.2f} | "
              f"${spread_price:>8.2f} | {spread_ticks:>11.1f} | ${data['tick_size']:>9.2f}")
    
    # Show different product variants and their tick sizes
    print(f"\n🎯 PRODUCT VARIANTS COMPARISON:")
    print("-" * 50)
    
    # Group by asset type and show tick size patterns
    asset_groups = es_contracts.groupby('asset').agg({
        'tick_size': ['count', 'min', 'max', 'mean'],
        'raw_symbol': 'first'
    }).round(4)
    
    print(f"{'Asset':>6} | {'Count':>5} | {'Min Tick':>8} | {'Max Tick':>8} | {'Avg Tick':>8} | {'Example':>10}")
    print("-" * 65)
    
    for asset in asset_groups.index:
        count = int(asset_groups.loc[asset, ('tick_size', 'count')])
        min_tick = asset_groups.loc[asset, ('tick_size', 'min')]
        max_tick = asset_groups.loc[asset, ('tick_size', 'max')]
        avg_tick = asset_groups.loc[asset, ('tick_size', 'mean')]
        example = asset_groups.loc[asset, ('raw_symbol', 'first')]
        
        print(f"{asset:>6} | {count:>5} | ${min_tick:>7.4f} | ${max_tick:>7.4f} | "
              f"${avg_tick:>7.4f} | {example:>10}")
    
    # Practical calculation examples
    print(f"\n🧮 PRACTICAL CALCULATIONS:")
    print("-" * 50)
    
    # Example: Position sizing based on tick value
    contract_multiplier = 50  # ES contract multiplier (50 * index value)
    
    print(f"ES Contract Multiplier: {contract_multiplier}")
    print(f"Standard ES Tick Size: $0.25")
    print(f"Tick Value: $0.25 × {contract_multiplier} = ${0.25 * contract_multiplier}")
    print()
    
    # Risk calculations
    risk_per_tick = 0.25 * contract_multiplier
    max_risk_dollars = 500  # Maximum risk per trade
    max_ticks_risk = max_risk_dollars / risk_per_tick
    
    print(f"Risk Management Example:")
    print(f"   Max risk per trade: ${max_risk_dollars}")
    print(f"   Risk per tick: ${risk_per_tick}")
    print(f"   Max ticks at risk: {max_ticks_risk:.1f} ticks")
    print(f"   Stop loss distance: {max_ticks_risk * 0.25:.2f} points")
    
    # Cross-contract comparison
    print(f"\n📊 CROSS-CONTRACT LIQUIDITY COMPARISON:")
    print("-" * 50)
    
    # Simulate different spreads for comparison
    contracts = [
        {'name': 'ESM5 (Front Month)', 'spread_ticks': 1.0, 'tick_size': 0.25},
        {'name': 'ESU5 (Next Month)', 'spread_ticks': 1.2, 'tick_size': 0.25},
        {'name': 'ESZ5 (Back Month)', 'spread_ticks': 2.0, 'tick_size': 0.25},
        {'name': 'ESR (Micro)', 'spread_ticks': 1.0, 'tick_size': 0.0025},
    ]
    
    print(f"{'Contract':>20} | {'Spread (Ticks)':>13} | {'Spread ($)':>10} | {'Liquidity':>10}")
    print("-" * 65)
    
    for contract in contracts:
        spread_dollars = contract['spread_ticks'] * contract['tick_size']
        liquidity = "High" if contract['spread_ticks'] <= 1.0 else "Medium" if contract['spread_ticks'] <= 1.5 else "Low"
        
        print(f"{contract['name']:>20} | {contract['spread_ticks']:>12.1f} | "
              f"${spread_dollars:>9.4f} | {liquidity:>10}")
    
    print(f"\n🎯 KEY TAKEAWAYS:")
    print("-" * 50)
    print(f"✅ Definition schema provides essential tick size data")
    print(f"✅ Standard ES: $0.25 tick = ${0.25 * contract_multiplier} per contract")
    print(f"✅ Micro ES (ESR): $0.0025 tick = ${0.0025 * contract_multiplier} per contract")
    print(f"✅ Normalize spreads to ticks for fair comparison")
    print(f"✅ Use tick data for position sizing and risk management")
    print(f"✅ Front month contracts typically most liquid (lowest spread)")
    
    print(f"\n💡 IMPLEMENTATION TIPS:")
    print("-" * 50)
    print(f"🔹 Cache definition data to avoid repeated API calls")
    print(f"🔹 Update definitions periodically for new contracts")
    print(f"🔹 Use instrument_id for reliable contract identification")
    print(f"🔹 Monitor spread changes for liquidity assessment")
    print(f"🔹 Consider tick value in algorithmic trading strategies")

if __name__ == "__main__":
    demonstrate_tick_calculations() 