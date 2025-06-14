#!/usr/bin/env python3
"""
Dataset Symbol Discovery Tool
Discover all available symbols across different Databento datasets
Based on Databento's dataset symbols example
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

import databento as db
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict

def discover_dataset_symbols():
    """Discover symbols across multiple datasets"""
    print("🔍 DATASET SYMBOL DISCOVERY")
    print("="*60)
    
    client = db.Historical()
    
    # Define datasets to analyze
    datasets = {
        "GLBX.MDP3": "CME Globex Futures & Options",
        "XNAS.ITCH": "NASDAQ Equities", 
        "DBEQ.BASIC": "Databento Equities Basic",
        "OPRA.PILLAR": "US Options"
    }
    
    analysis_date = "2024-12-01"
    
    print(f"📅 Analysis date: {analysis_date}")
    print(f"🎯 Target datasets: {len(datasets)}")
    
    all_results = {}
    
    for dataset_code, dataset_name in datasets.items():
        print(f"\n📊 Analyzing {dataset_code} ({dataset_name})...")
        
        try:
            # Get definition data for all symbols
            data = client.timeseries.get_range(
                dataset=dataset_code,
                symbols="ALL_SYMBOLS",
                start=analysis_date,
                schema="definition",
            )
            
            # Create symbol map
            symbol_map = {msg.raw_symbol: msg for msg in data}
            symbols = sorted(symbol_map.keys())
            
            print(f"   ✅ Found {len(symbols):,} symbols")
            
            # Analyze symbol patterns
            symbol_analysis = analyze_symbol_patterns(symbols, symbol_map)
            
            all_results[dataset_code] = {
                'name': dataset_name,
                'symbol_count': len(symbols),
                'symbols': symbols,
                'symbol_map': symbol_map,
                'analysis': symbol_analysis
            }
            
            # Show sample symbols
            print(f"   📋 Sample symbols: {symbols[:10]}")
            
            if dataset_code == "GLBX.MDP3":
                # Special analysis for futures
                analyze_futures_symbols(symbol_map)
            
        except Exception as e:
            print(f"   ❌ Error analyzing {dataset_code}: {e}")
            all_results[dataset_code] = {
                'name': dataset_name,
                'error': str(e)
            }
    
    # Cross-dataset comparison
    print(f"\n📈 CROSS-DATASET COMPARISON:")
    print("-" * 70)
    print(f"{'Dataset':>15} | {'Name':>25} | {'Symbol Count':>12} | {'Status':>10}")
    print("-" * 70)
    
    for dataset_code, result in all_results.items():
        if 'error' in result:
            print(f"{dataset_code:>15} | {result['name']:>25} | {'N/A':>12} | {'Error':>10}")
        else:
            print(f"{dataset_code:>15} | {result['name']:>25} | {result['symbol_count']:>12,} | {'Success':>10}")
    
    # Export comprehensive results
    export_symbol_discovery_results(all_results, analysis_date)
    
    return all_results

def analyze_symbol_patterns(symbols, symbol_map):
    """Analyze patterns in symbol names and characteristics"""
    analysis = {
        'length_distribution': defaultdict(int),
        'prefix_patterns': defaultdict(int),
        'instrument_classes': defaultdict(int),
        'character_patterns': defaultdict(int)
    }
    
    for symbol in symbols:
        # Length distribution
        length = len(symbol)
        analysis['length_distribution'][length] += 1
        
        # Prefix patterns (first 2-3 characters)
        if length >= 2:
            analysis['prefix_patterns'][symbol[:2]] += 1
        
        # Character patterns
        if symbol.isalpha():
            analysis['character_patterns']['all_alpha'] += 1
        elif symbol.isalnum():
            analysis['character_patterns']['alphanumeric'] += 1
        elif any(c in symbol for c in ['.', '-', '_']):
            analysis['character_patterns']['with_separators'] += 1
        else:
            analysis['character_patterns']['other'] += 1
        
        # Instrument class analysis
        if symbol in symbol_map:
            msg = symbol_map[symbol]
            if hasattr(msg, 'instrument_class'):
                analysis['instrument_classes'][str(msg.instrument_class)] += 1
    
    return analysis

def analyze_futures_symbols(symbol_map):
    """Special analysis for futures symbols in GLBX.MDP3"""
    print(f"\n   🎯 FUTURES SYMBOL ANALYSIS:")
    
    futures_symbols = []
    es_symbols = []
    
    for symbol, msg in symbol_map.items():
        if hasattr(msg, 'instrument_class') and str(msg.instrument_class) == 'InstrumentClass.FUTURE':
            futures_symbols.append(symbol)
            
            # Look for ES-related symbols
            if symbol.startswith('ES'):
                es_symbols.append(symbol)
    
    print(f"      📊 Total futures: {len(futures_symbols):,}")
    print(f"      📊 ES futures: {len(es_symbols)}")
    
    if es_symbols:
        print(f"      📋 ES symbols: {sorted(es_symbols)[:20]}")  # Show first 20
    
    # Analyze futures patterns
    if futures_symbols:
        # Group by root symbol
        root_patterns = defaultdict(list)
        for symbol in futures_symbols:
            # Extract root (typically first 2-3 characters)
            if len(symbol) >= 2:
                root = symbol[:2]
                root_patterns[root].append(symbol)
        
        # Show top futures roots
        top_roots = sorted(root_patterns.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        print(f"      📈 Top futures roots:")
        for root, symbols in top_roots:
            print(f"         {root}: {len(symbols)} contracts")

def discover_es_symbols_comprehensive():
    """Comprehensive ES symbol discovery across datasets"""
    print(f"\n🎯 COMPREHENSIVE ES SYMBOL DISCOVERY")
    print("-" * 60)
    
    client = db.Historical()
    analysis_date = "2024-12-01"
    
    # Focus on datasets likely to have ES futures
    futures_datasets = ["GLBX.MDP3"]
    
    all_es_symbols = {}
    
    for dataset in futures_datasets:
        print(f"\n📊 Searching {dataset} for ES symbols...")
        
        try:
            data = client.timeseries.get_range(
                dataset=dataset,
                symbols="ALL_SYMBOLS",
                start=analysis_date,
                schema="definition",
            )
            
            symbol_map = {msg.raw_symbol: msg for msg in data}
            
            # Find all ES-related symbols
            es_symbols = {}
            for symbol, msg in symbol_map.items():
                if symbol.startswith('ES'):
                    es_symbols[symbol] = msg
            
            print(f"   ✅ Found {len(es_symbols)} ES symbols")
            
            if es_symbols:
                all_es_symbols[dataset] = es_symbols
                
                # Detailed ES analysis
                analyze_es_symbol_details(es_symbols)
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return all_es_symbols

def analyze_es_symbol_details(es_symbols):
    """Detailed analysis of ES symbol characteristics"""
    print(f"   📋 ES SYMBOL BREAKDOWN:")
    
    # Group by asset type
    asset_groups = defaultdict(list)
    expiration_patterns = defaultdict(list)
    tick_sizes = defaultdict(list)
    
    for symbol, msg in es_symbols.items():
        # Asset grouping
        if hasattr(msg, 'asset'):
            asset_groups[msg.asset].append(symbol)
        
        # Expiration analysis
        if hasattr(msg, 'expiration') and msg.expiration:
            exp_date = pd.to_datetime(msg.expiration, unit='ns')
            exp_month = exp_date.strftime('%Y-%m')
            expiration_patterns[exp_month].append(symbol)
        
        # Tick size analysis
        if hasattr(msg, 'min_price_increment'):
            tick_size = msg.min_price_increment
            tick_sizes[tick_size].append(symbol)
    
    # Display asset breakdown
    print(f"      📊 By Asset Type:")
    for asset, symbols in sorted(asset_groups.items()):
        print(f"         {asset}: {len(symbols)} symbols")
        if len(symbols) <= 10:
            print(f"            {sorted(symbols)}")
        else:
            print(f"            {sorted(symbols)[:5]} ... (+{len(symbols)-5} more)")
    
    # Display tick size breakdown
    print(f"      💰 By Tick Size:")
    for tick_size, symbols in sorted(tick_sizes.items()):
        print(f"         ${tick_size}: {len(symbols)} symbols")
    
    # Display expiration patterns
    if expiration_patterns:
        print(f"      📅 By Expiration Month:")
        for exp_month, symbols in sorted(expiration_patterns.items())[:6]:  # Show first 6 months
            print(f"         {exp_month}: {len(symbols)} symbols")

def export_symbol_discovery_results(results, analysis_date):
    """Export comprehensive symbol discovery results"""
    print(f"\n📁 EXPORTING RESULTS...")
    
    base_path = os.path.dirname(__file__)
    
    # Export summary
    summary_data = []
    for dataset_code, result in results.items():
        if 'error' not in result:
            summary_data.append({
                'dataset': dataset_code,
                'name': result['name'],
                'symbol_count': result['symbol_count'],
                'analysis_date': analysis_date
            })
    
    summary_df = pd.DataFrame(summary_data)
    summary_path = os.path.join(base_path, "dataset_symbol_summary.csv")
    summary_df.to_csv(summary_path, index=False)
    print(f"   ✅ Summary: {summary_path}")
    
    # Export detailed symbol lists for each dataset
    for dataset_code, result in results.items():
        if 'error' not in result and 'symbols' in result:
            # Create detailed DataFrame
            detailed_data = []
            for symbol in result['symbols']:
                if symbol in result['symbol_map']:
                    msg = result['symbol_map'][symbol]
                    detailed_data.append({
                        'raw_symbol': symbol,
                        'instrument_id': getattr(msg, 'instrument_id', None),
                        'instrument_class': str(getattr(msg, 'instrument_class', None)),
                        'asset': getattr(msg, 'asset', None),
                        'min_price_increment': getattr(msg, 'min_price_increment', None),
                        'expiration': getattr(msg, 'expiration', None),
                        'security_type': getattr(msg, 'security_type', None)
                    })
            
            if detailed_data:
                detailed_df = pd.DataFrame(detailed_data)
                detailed_path = os.path.join(base_path, f"symbols_{dataset_code.replace('.', '_').lower()}.csv")
                detailed_df.to_csv(detailed_path, index=False)
                print(f"   ✅ {dataset_code}: {detailed_path}")

def main():
    """Main execution function"""
    print("🚀 STARTING COMPREHENSIVE SYMBOL DISCOVERY")
    print("="*60)
    
    # Step 1: Discover symbols across datasets
    dataset_results = discover_dataset_symbols()
    
    # Step 2: Focused ES symbol discovery
    es_results = discover_es_symbols_comprehensive()
    
    # Step 3: Generate recommendations
    print(f"\n🎯 SYMBOL DISCOVERY RECOMMENDATIONS:")
    print("-" * 60)
    print(f"✅ Use 'ALL_SYMBOLS' for comprehensive dataset exploration")
    print(f"✅ Filter by instrument_class for specific asset types")
    print(f"✅ Monitor expiration dates for futures/options")
    print(f"✅ Consider tick sizes for trading strategy design")
    print(f"✅ Build symbol maps for efficient lookups")
    print(f"✅ Cache symbol data to avoid repeated API calls")
    
    print(f"\n💡 NEXT STEPS:")
    print("-" * 50)
    print(f"🔹 Use discovered symbols for targeted data requests")
    print(f"🔹 Build trading universe filters based on characteristics")
    print(f"🔹 Monitor symbol changes over time")
    print(f"🔹 Integrate with liquidity analysis for optimal selection")

if __name__ == "__main__":
    main() 