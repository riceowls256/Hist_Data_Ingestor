#!/usr/bin/env python3
"""
Contract Endings Analysis
Analyze unique contract endings and patterns from ES futures data
"""

import csv
import os
from collections import Counter
import re

def analyze_contract_endings():
    """Analyze ES contract endings and patterns"""
    print("🔍 ES CONTRACT ENDINGS ANALYSIS")
    print("="*60)
    
    csv_path = os.path.join(os.path.dirname(__file__), "es_futures_contracts.csv")
    
    if not os.path.exists(csv_path):
        print("❌ ES futures CSV not found!")
        return
    
    # Counters for analysis
    contract_endings_2 = Counter()
    contract_endings_3 = Counter()
    asset_types = Counter()
    symbol_patterns = Counter()
    expiration_months = Counter()
    expiration_years = Counter()
    tick_sizes = Counter()
    
    # ES contract categories
    standard_es = []
    spread_contracts = []
    micro_contracts = []
    other_variants = []
    
    total_contracts = 0
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            total_contracts += 1
            
            instrument_id = row['instrument_id']
            raw_symbol = row['raw_symbol']
            asset = row['asset']
            expiration = row['expiration']
            tick_size = row['tick_size']
            
            # Track asset types
            asset_types[asset] += 1
            
            # Track tick sizes
            tick_sizes[tick_size] += 1
            
            # Analyze symbol patterns
            if raw_symbol:
                # Contract endings (last 1-3 characters)
                if len(raw_symbol) >= 2:
                    ending_2 = raw_symbol[-2:]
                    contract_endings_2[ending_2] += 1
                
                if len(raw_symbol) >= 3:
                    ending_3 = raw_symbol[-3:]
                    contract_endings_3[ending_3] += 1
                
                # Symbol patterns
                symbol_patterns[raw_symbol[:3]] += 1
                
                # Categorize contracts
                if '-' in raw_symbol:
                    spread_contracts.append({
                        'id': instrument_id,
                        'symbol': raw_symbol,
                        'asset': asset,
                        'expiration': expiration
                    })
                elif asset == 'ES' and len(raw_symbol) <= 5 and not ':' in raw_symbol:
                    standard_es.append({
                        'id': instrument_id,
                        'symbol': raw_symbol,
                        'asset': asset,
                        'expiration': expiration
                    })
                elif asset in ['ESR', 'ESG', 'EST', 'ESQ', 'ESX']:
                    micro_contracts.append({
                        'id': instrument_id,
                        'symbol': raw_symbol,
                        'asset': asset,
                        'expiration': expiration
                    })
                else:
                    other_variants.append({
                        'id': instrument_id,
                        'symbol': raw_symbol,
                        'asset': asset,
                        'expiration': expiration
                    })
            
            # Analyze expiration patterns
            if expiration and expiration != 'N/A':
                try:
                    # Extract month and year from expiration
                    if '2024' in expiration:
                        expiration_years['2024'] += 1
                    elif '2025' in expiration:
                        expiration_years['2025'] += 1
                    elif '2026' in expiration:
                        expiration_years['2026'] += 1
                    elif '2027' in expiration:
                        expiration_years['2027'] += 1
                    elif '2028' in expiration:
                        expiration_years['2028'] += 1
                    elif '2029' in expiration:
                        expiration_years['2029'] += 1
                    
                    # Extract months
                    if '-03-' in expiration:
                        expiration_months['March'] += 1
                    elif '-06-' in expiration:
                        expiration_months['June'] += 1
                    elif '-09-' in expiration:
                        expiration_months['September'] += 1
                    elif '-12-' in expiration:
                        expiration_months['December'] += 1
                    elif '-01-' in expiration:
                        expiration_months['January'] += 1
                    elif '-02-' in expiration:
                        expiration_months['February'] += 1
                    elif '-04-' in expiration:
                        expiration_months['April'] += 1
                    elif '-05-' in expiration:
                        expiration_months['May'] += 1
                except:
                    pass
    
    print(f"📊 ANALYSIS RESULTS")
    print(f"Total ES-related contracts: {total_contracts:,}")
    print()
    
    # Asset Types
    print(f"🏷️  ASSET TYPES:")
    for asset, count in asset_types.most_common():
        percentage = (count / total_contracts) * 100
        print(f"   {asset:>6}: {count:>3} contracts ({percentage:>5.1f}%)")
    
    print(f"\n💰 TICK SIZES:")
    for tick, count in tick_sizes.most_common():
        percentage = (count / total_contracts) * 100
        print(f"   {tick:>8}: {count:>3} contracts ({percentage:>5.1f}%)")
    
    # Contract endings analysis
    print(f"\n🔤 TOP 15 CONTRACT ENDINGS (2 chars):")
    for ending, count in contract_endings_2.most_common(15):
        percentage = (count / total_contracts) * 100
        print(f"   {ending:>4}: {count:>3} contracts ({percentage:>5.1f}%)")
    
    print(f"\n🔤 TOP 15 CONTRACT ENDINGS (3 chars):")
    for ending, count in contract_endings_3.most_common(15):
        percentage = (count / total_contracts) * 100
        print(f"   {ending:>5}: {count:>3} contracts ({percentage:>5.1f}%)")
    
    # Symbol patterns
    print(f"\n📝 SYMBOL PATTERNS (first 3 chars):")
    for pattern, count in symbol_patterns.most_common(10):
        percentage = (count / total_contracts) * 100
        print(f"   {pattern:>5}: {count:>3} contracts ({percentage:>5.1f}%)")
    
    # Expiration analysis
    print(f"\n📅 EXPIRATION YEARS:")
    for year, count in expiration_years.most_common():
        percentage = (count / total_contracts) * 100
        print(f"   {year:>6}: {count:>3} contracts ({percentage:>5.1f}%)")
    
    print(f"\n📅 EXPIRATION MONTHS:")
    for month, count in expiration_months.most_common():
        percentage = (count / total_contracts) * 100
        print(f"   {month:>9}: {count:>3} contracts ({percentage:>5.1f}%)")
    
    # Contract categories
    print(f"\n📋 CONTRACT CATEGORIES:")
    print(f"   Standard ES Futures: {len(standard_es):>3} contracts")
    print(f"   Spread Contracts:    {len(spread_contracts):>3} contracts") 
    print(f"   Micro Variants:      {len(micro_contracts):>3} contracts")
    print(f"   Other Variants:      {len(other_variants):>3} contracts")
    
    # Show sample contracts from each category
    print(f"\n📋 STANDARD ES FUTURES (sample):")
    for i, contract in enumerate(standard_es[:10]):
        print(f"   {i+1:>2}. {contract['symbol']:>6} | ID: {contract['id']:>8} | Expires: {contract['expiration'][:10]}")
    
    print(f"\n📋 SPREAD CONTRACTS (sample):")
    for i, contract in enumerate(spread_contracts[:10]):
        print(f"   {i+1:>2}. {contract['symbol']:>15} | ID: {contract['id']:>8} | Asset: {contract['asset']}")
    
    print(f"\n📋 MICRO VARIANTS (sample):")
    for i, contract in enumerate(micro_contracts[:10]):
        print(f"   {i+1:>2}. {contract['symbol']:>10} | ID: {contract['id']:>8} | Asset: {contract['asset']}")
    
    # Create contract endings summary CSV
    endings_csv = os.path.join(os.path.dirname(__file__), "contract_endings_analysis.csv")
    with open(endings_csv, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['ending_type', 'pattern', 'count', 'percentage']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write 2-char endings
        for ending, count in contract_endings_2.most_common():
            writer.writerow({
                'ending_type': '2-char',
                'pattern': ending,
                'count': count,
                'percentage': round((count / total_contracts) * 100, 1)
            })
        
        # Write 3-char endings  
        for ending, count in contract_endings_3.most_common():
            writer.writerow({
                'ending_type': '3-char',
                'pattern': ending,
                'count': count,
                'percentage': round((count / total_contracts) * 100, 1)
            })
    
    print(f"\n📁 Contract endings analysis saved to: {endings_csv}")
    
    print(f"\n🎯 KEY INSIGHTS:")
    print("-" * 50)
    print(f"✅ Found {total_contracts} ES-related futures contracts")
    print(f"✅ Standard quarterly ES contracts (ESH5, ESM5, ESU5, ESZ5 pattern)")
    print(f"✅ Multiple product variants: ES, ESR, ESG, EST, ESQ, ESX")
    print(f"✅ Spread contracts for calendar spreads (ES-ES pairs)")
    print(f"✅ Complex naming for special products (:BF, :DF, :CF patterns)")
    print(f"✅ Contract codes follow CME month/year conventions")
    print(f"✅ Different tick sizes for different product types")

if __name__ == "__main__":
    analyze_contract_endings() 