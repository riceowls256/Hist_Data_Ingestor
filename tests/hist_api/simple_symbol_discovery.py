#!/usr/bin/env python3
"""
Simple Symbol Discovery
Demonstrates how to get all symbols for a dataset using the definition schema
Based on Databento's dataset symbols example
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

import databento as db
import pandas as pd

def discover_symbols_simple():
    """Simple symbol discovery for a single dataset"""
    print("🔍 SIMPLE SYMBOL DISCOVERY")
    print("="*50)
    
    # Create a historical client
    client = db.Historical()
    
    # Choose dataset - start with CME Globex for futures
    dataset = "GLBX.MDP3"
    analysis_date = "2024-12-01"
    
    print(f"📊 Dataset: {dataset}")
    print(f"📅 Date: {analysis_date}")
    
    try:
        print(f"\n⏳ Downloading definition schema for all symbols...")
        
        # Download definition schema for all symbols
        data = client.timeseries.get_range(
            dataset=dataset,
            symbols="ALL_SYMBOLS",
            start=analysis_date,
            schema="definition",
        )
        
        print(f"✅ Retrieved definition data")
        
        # Create a map of raw_symbol -> InstrumentDefMsgs
        symbol_map = {msg.raw_symbol: msg for msg in data}
        
        # Get all symbols
        symbols = sorted(symbol_map.keys())
        
        # Print out the symbol count and sample symbols
        print(f"\n📈 RESULTS:")
        print(f"   Total symbol count for {dataset} = {len(symbols):,}")
        print(f"   First 10 symbols: {symbols[:10]}")
        print(f"   Last 10 symbols: {symbols[-10:]}")
        
        # Analyze symbol characteristics
        analyze_symbol_characteristics(symbols, symbol_map)
        
        # Focus on ES symbols (our area of interest)
        find_es_symbols(symbols, symbol_map)
        
        # Export results
        export_symbol_data(symbols, symbol_map, dataset, analysis_date)
        
        return symbols, symbol_map
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None

def analyze_symbol_characteristics(symbols, symbol_map):
    """Analyze basic characteristics of discovered symbols"""
    print(f"\n📊 SYMBOL CHARACTERISTICS:")
    
    # Length distribution
    lengths = [len(s) for s in symbols]
    print(f"   Symbol length range: {min(lengths)} - {max(lengths)} characters")
    print(f"   Average length: {sum(lengths)/len(lengths):.1f} characters")
    
    # Instrument class breakdown
    instrument_classes = {}
    for symbol, msg in symbol_map.items():
        if hasattr(msg, 'instrument_class'):
            class_name = str(msg.instrument_class)
            instrument_classes[class_name] = instrument_classes.get(class_name, 0) + 1
    
    print(f"\n   📋 Instrument Classes:")
    for class_name, count in sorted(instrument_classes.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(symbols)) * 100
        print(f"      {class_name}: {count:,} ({percentage:.1f}%)")
    
    # Common prefixes
    prefixes = {}
    for symbol in symbols:
        if len(symbol) >= 2:
            prefix = symbol[:2]
            prefixes[prefix] = prefixes.get(prefix, 0) + 1
    
    top_prefixes = sorted(prefixes.items(), key=lambda x: x[1], reverse=True)[:10]
    print(f"\n   🔤 Top 10 Symbol Prefixes:")
    for prefix, count in top_prefixes:
        print(f"      {prefix}: {count:,} symbols")

def find_es_symbols(symbols, symbol_map):
    """Find and analyze ES-related symbols"""
    print(f"\n🎯 ES SYMBOL ANALYSIS:")
    
    # Find ES symbols
    es_symbols = [s for s in symbols if s.startswith('ES')]
    print(f"   Found {len(es_symbols)} ES-related symbols")
    
    if es_symbols:
        print(f"   📋 ES symbols: {sorted(es_symbols)[:20]}")  # Show first 20
        
        # Analyze ES symbol details
        es_assets = {}
        es_tick_sizes = {}
        
        for symbol in es_symbols:
            if symbol in symbol_map:
                msg = symbol_map[symbol]
                
                # Asset analysis
                if hasattr(msg, 'asset'):
                    asset = msg.asset
                    es_assets[asset] = es_assets.get(asset, 0) + 1
                
                # Tick size analysis
                if hasattr(msg, 'min_price_increment'):
                    tick = msg.min_price_increment
                    es_tick_sizes[tick] = es_tick_sizes.get(tick, 0) + 1
        
        print(f"\n   📊 ES Asset Breakdown:")
        for asset, count in sorted(es_assets.items()):
            print(f"      {asset}: {count} contracts")
        
        print(f"\n   💰 ES Tick Size Distribution:")
        for tick, count in sorted(es_tick_sizes.items()):
            print(f"      ${tick}: {count} contracts")

def export_symbol_data(symbols, symbol_map, dataset, analysis_date):
    """Export symbol data to CSV for further analysis"""
    print(f"\n📁 EXPORTING DATA:")
    
    # Create DataFrame with symbol details
    symbol_data = []
    for symbol in symbols:
        if symbol in symbol_map:
            msg = symbol_map[symbol]
            symbol_data.append({
                'raw_symbol': symbol,
                'instrument_id': getattr(msg, 'instrument_id', None),
                'instrument_class': str(getattr(msg, 'instrument_class', None)),
                'asset': getattr(msg, 'asset', None),
                'min_price_increment': getattr(msg, 'min_price_increment', None),
                'expiration': getattr(msg, 'expiration', None),
                'security_type': getattr(msg, 'security_type', None),
                'dataset': dataset,
                'analysis_date': analysis_date
            })
    
    # Export all symbols
    df = pd.DataFrame(symbol_data)
    all_symbols_path = os.path.join(os.path.dirname(__file__), f"all_symbols_{dataset.replace('.', '_').lower()}.csv")
    df.to_csv(all_symbols_path, index=False)
    print(f"   ✅ All symbols: {all_symbols_path}")
    
    # Export ES symbols only
    es_df = df[df['raw_symbol'].str.startswith('ES', na=False)]
    if not es_df.empty:
        es_symbols_path = os.path.join(os.path.dirname(__file__), f"es_symbols_discovered.csv")
        es_df.to_csv(es_symbols_path, index=False)
        print(f"   ✅ ES symbols: {es_symbols_path}")
    
    # Export futures only
    futures_df = df[df['instrument_class'].str.contains('FUTURE', na=False)]
    if not futures_df.empty:
        futures_path = os.path.join(os.path.dirname(__file__), f"futures_symbols_{dataset.replace('.', '_').lower()}.csv")
        futures_df.to_csv(futures_path, index=False)
        print(f"   ✅ Futures: {futures_path}")

def compare_with_existing_es_data():
    """Compare discovered symbols with our existing ES analysis"""
    print(f"\n🔄 COMPARING WITH EXISTING ES DATA:")
    
    # Try to load our existing ES contracts
    existing_path = os.path.join(os.path.dirname(__file__), "es_futures_contracts.csv")
    discovered_path = os.path.join(os.path.dirname(__file__), "es_symbols_discovered.csv")
    
    if os.path.exists(existing_path) and os.path.exists(discovered_path):
        existing_df = pd.read_csv(existing_path)
        discovered_df = pd.read_csv(discovered_path)
        
        existing_symbols = set(existing_df['raw_symbol'])
        discovered_symbols = set(discovered_df['raw_symbol'])
        
        print(f"   📊 Existing ES contracts: {len(existing_symbols)}")
        print(f"   📊 Discovered ES symbols: {len(discovered_symbols)}")
        
        # Find differences
        only_in_existing = existing_symbols - discovered_symbols
        only_in_discovered = discovered_symbols - existing_symbols
        common = existing_symbols & discovered_symbols
        
        print(f"   📊 Common symbols: {len(common)}")
        print(f"   📊 Only in existing: {len(only_in_existing)}")
        print(f"   📊 Only in discovered: {len(only_in_discovered)}")
        
        if only_in_discovered:
            print(f"   🆕 New symbols found: {sorted(list(only_in_discovered))[:10]}")
    
    else:
        print(f"   💡 Run the definition analysis first to compare results")

def main():
    """Main execution function"""
    print("🚀 STARTING SIMPLE SYMBOL DISCOVERY")
    print("="*50)
    
    # Discover symbols
    symbols, symbol_map = discover_symbols_simple()
    
    if symbols:
        # Compare with existing data
        compare_with_existing_es_data()
        
        print(f"\n🎯 KEY TAKEAWAYS:")
        print("-" * 40)
        print(f"✅ 'ALL_SYMBOLS' retrieves complete symbol universe")
        print(f"✅ Definition schema provides rich metadata")
        print(f"✅ Symbol maps enable efficient lookups")
        print(f"✅ Filter by instrument_class for specific types")
        print(f"✅ Cache results to avoid repeated API calls")
        
        print(f"\n💡 NEXT STEPS:")
        print("-" * 40)
        print(f"🔹 Use discovered symbols for targeted analysis")
        print(f"🔹 Build trading universe filters")
        print(f"🔹 Monitor symbol changes over time")
        print(f"🔹 Integrate with liquidity analysis")

if __name__ == "__main__":
    main() 