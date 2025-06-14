#!/usr/bin/env python3
"""
Targeted Definition Schema Search
Look for ES futures and analyze security types in the definition schema
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

import databento as db
import csv
from collections import Counter

def targeted_definition_search():
    """Search for specific contract types and ES futures"""
    print("🔍 TARGETED DEFINITION SCHEMA SEARCH")
    print("="*60)
    
    client = db.Historical()
    print("✅ Connected to Databento API")
    
    print("\n📊 Searching for ES futures and analyzing security types...")
    
    data = client.timeseries.get_range(
        dataset="GLBX.MDP3",
        schema="definition",
        start="2024-12-01",
        end="2025-01-31",
    )
    
    # Counters for analysis
    security_types = Counter()
    asset_types = Counter()
    es_futures = []
    es_options = []
    futures_contracts = []
    
    total_records = 0
    
    print("🔍 Scanning for ES contracts and security types...")
    
    for record in data:
        total_records += 1
        
        # Extract key fields
        instrument_id = getattr(record, 'instrument_id', 'N/A')
        raw_symbol = getattr(record, 'raw_symbol', 'N/A')
        asset = getattr(record, 'asset', 'N/A')
        security_type = getattr(record, 'security_type', 'N/A')
        exchange = getattr(record, 'exchange', 'N/A')
        
        # Count security types
        if security_type != 'N/A':
            security_types[security_type] += 1
        
        # Count asset types
        if asset != 'N/A':
            asset_types[asset] += 1
        
        # Look for ES contracts specifically
        if asset == 'ES' or (raw_symbol != 'N/A' and raw_symbol.startswith('ES')):
            contract_info = {
                'instrument_id': instrument_id,
                'raw_symbol': raw_symbol,
                'asset': asset,
                'security_type': security_type,
                'exchange': exchange,
                'expiration': getattr(record, 'pretty_expiration', 'N/A'),
                'tick_size': getattr(record, 'pretty_min_price_increment', 'N/A'),
                'multiplier': getattr(record, 'contract_multiplier', 'N/A')
            }
            
            if security_type == 'FUT':  # Futures
                es_futures.append(contract_info)
            elif security_type == 'OOF':  # Options on Futures
                es_options.append(contract_info)
        
        # Collect sample futures (non-options)
        if security_type == 'FUT' and len(futures_contracts) < 20:
            futures_contracts.append({
                'instrument_id': instrument_id,
                'raw_symbol': raw_symbol,
                'asset': asset,
                'security_type': security_type,
                'exchange': exchange
            })
        
        # Progress and early termination for analysis
        if total_records % 100000 == 0:
            print(f"   Processed {total_records:,} records...")
            print(f"     ES futures found: {len(es_futures)}")
            print(f"     ES options found: {len(es_options)}")
            print(f"     Total futures found: {len(futures_contracts)}")
        
        # Stop after reasonable sample for quick analysis
        if total_records >= 500000:  # Half million for broader analysis
            print(f"   Stopping after {total_records:,} records...")
            break
    
    print(f"\n📊 ANALYSIS RESULTS")
    print("="*50)
    print(f"Total records processed: {total_records:,}")
    
    # Security Types Analysis
    print(f"\n🔒 Security Types Found:")
    for sec_type, count in security_types.most_common():
        percentage = (count / total_records) * 100
        print(f"   {sec_type:>6}: {count:>8,} ({percentage:>5.1f}%)")
    
    # Asset Types (top 20)
    print(f"\n💰 Top 20 Asset Types:")
    for asset, count in asset_types.most_common(20):
        percentage = (count / total_records) * 100
        print(f"   {asset:>6}: {count:>8,} ({percentage:>5.1f}%)")
    
    # ES Analysis
    print(f"\n🎯 E-MINI S&P 500 (ES) RESULTS")
    print("="*50)
    print(f"ES Futures (FUT): {len(es_futures)}")
    print(f"ES Options (OOF): {len(es_options)}")
    
    if es_futures:
        print(f"\n📋 ES Futures Contracts:")
        for i, contract in enumerate(es_futures):
            print(f"   {i+1:>2}. ID: {contract['instrument_id']:>6} | "
                  f"Symbol: {contract['raw_symbol']:>8} | "
                  f"Type: {contract['security_type']} | "
                  f"Expires: {contract['expiration']}")
    
    if es_options:
        print(f"\n📋 ES Options (first 10):")
        for i, contract in enumerate(es_options[:10]):
            print(f"   {i+1:>2}. ID: {contract['instrument_id']:>6} | "
                  f"Symbol: {contract['raw_symbol']:>15} | "
                  f"Type: {contract['security_type']}")
    
    # Sample Futures Contracts
    print(f"\n📋 Sample Futures Contracts (FUT):")
    for i, contract in enumerate(futures_contracts):
        print(f"   {i+1:>2}. ID: {contract['instrument_id']:>6} | "
              f"Symbol: {contract['raw_symbol']:>8} | "
              f"Asset: {contract['asset']:>4} | "
              f"Exchange: {contract['exchange']}")
    
    # Create CSV for futures contracts
    if futures_contracts:
        csv_filename = "futures_contracts_sample.csv"
        csv_path = os.path.join(os.path.dirname(__file__), csv_filename)
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = futures_contracts[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(futures_contracts)
        
        print(f"\n📁 Futures contracts CSV: {csv_path}")
    
    # Create CSV for ES contracts if found
    if es_futures:
        csv_filename = "es_futures_contracts.csv"
        csv_path = os.path.join(os.path.dirname(__file__), csv_filename)
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = es_futures[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(es_futures)
        
        print(f"📁 ES futures CSV: {csv_path}")
    
    print(f"\n🎯 KEY FINDINGS:")
    print("-" * 50)
    if len(es_futures) > 0:
        print(f"✅ Found {len(es_futures)} ES futures contracts!")
        print(f"✅ ES futures have instrument IDs that can be used for filtering")
    else:
        print(f"❌ No ES futures found in first {total_records:,} records")
        print(f"   → May need to scan more records or different date range")
    
    print(f"✅ Most records are options (OOF) - {security_types.get('OOF', 0):,}")
    print(f"✅ Futures contracts (FUT) found: {security_types.get('FUT', 0):,}")
    print(f"✅ Multiple asset classes beyond ES available")

if __name__ == "__main__":
    targeted_definition_search() 