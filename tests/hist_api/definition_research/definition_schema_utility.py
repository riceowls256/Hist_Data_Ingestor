#!/usr/bin/env python3
"""
Definition Schema Utility
Comprehensive utility for using definition schema to map contracts, months, and relationships
Essential for cross-referencing continuous contracts with specific months
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'src'))

import databento as db
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
import calendar

class DefinitionSchemaMapper:
    """Utility class for mapping contracts using definition schema"""
    
    def __init__(self, client=None):
        self.client = client or db.Historical()
        self.symbol_map = {}
        self.contract_chains = defaultdict(list)
        self.month_mappings = {}
        
    def load_definitions(self, dataset="GLBX.MDP3", date="2024-12-01", asset_filter=None):
        """Load definition data and create mappings"""
        print(f"🔍 Loading definition data for {dataset} on {date}")
        
        try:
            # Get all definitions
            data = self.client.timeseries.get_range(
                dataset=dataset,
                symbols="ALL_SYMBOLS",
                start=date,
                schema="definition",
            )
            
            # Create symbol map
            self.symbol_map = {msg.raw_symbol: msg for msg in data}
            print(f"   ✅ Loaded {len(self.symbol_map):,} symbol definitions")
            
            # Filter if requested
            if asset_filter:
                filtered_map = {}
                for symbol, msg in self.symbol_map.items():
                    if hasattr(msg, 'asset') and msg.asset and msg.asset.startswith(asset_filter):
                        filtered_map[symbol] = msg
                self.symbol_map = filtered_map
                print(f"   🎯 Filtered to {len(self.symbol_map):,} {asset_filter} symbols")
            
            # Build contract chains and month mappings
            self._build_contract_chains()
            self._build_month_mappings()
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error loading definitions: {e}")
            return False
    
    def _build_contract_chains(self):
        """Build contract chains by asset"""
        print(f"   📊 Building contract chains...")
        
        for symbol, msg in self.symbol_map.items():
            if hasattr(msg, 'asset') and hasattr(msg, 'instrument_class'):
                asset = msg.asset
                # Check for futures - handle different string representations
                instrument_class_str = str(msg.instrument_class)
                if 'FUTURE' in instrument_class_str.upper():
                    self.contract_chains[asset].append({
                        'symbol': symbol,
                        'instrument_id': msg.instrument_id,
                        'expiration': msg.expiration,
                        'tick_size': msg.min_price_increment,
                        'msg': msg
                    })
        
        # Sort chains by expiration
        for asset in self.contract_chains:
            self.contract_chains[asset].sort(key=lambda x: x['expiration'] or 0)
        
        print(f"   ✅ Built chains for {len(self.contract_chains)} assets")
        
        # Debug: Show what we found
        for asset, contracts in self.contract_chains.items():
            if contracts:  # Only show assets with contracts
                print(f"      {asset}: {len(contracts)} contracts")
                # Show first few contracts
                for contract in contracts[:3]:
                    print(f"         {contract['symbol']} (ID: {contract['instrument_id']})")
    
    def _build_month_mappings(self):
        """Build month code mappings"""
        # Standard futures month codes
        self.month_codes = {
            'F': 1,  'G': 2,  'H': 3,  'J': 4,  'K': 5,  'M': 6,
            'N': 7,  'Q': 8,  'U': 9,  'V': 10, 'X': 11, 'Z': 12
        }
        
        self.month_names = {
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }
        
        # Reverse mappings
        self.code_to_month = {v: k for k, v in self.month_codes.items()}
    
    def parse_contract_month(self, symbol):
        """Parse month and year from contract symbol"""
        # Handle different symbol formats
        # ESM5, ESU24, CLZ4, etc.
        
        if len(symbol) < 3:
            return None, None
        
        # Look for month code (letter) and year (number)
        month_code = None
        year_digits = None
        
        # Common patterns: ESM5, ESU24, CLZ4
        for i, char in enumerate(symbol):
            if char in self.month_codes and i < len(symbol) - 1:
                month_code = char
                # Get year digits after month code
                remaining = symbol[i+1:]
                if remaining.isdigit():
                    year_digits = remaining
                    break
        
        if not month_code or not year_digits:
            return None, None
        
        # Convert to full year
        year_num = int(year_digits)
        if year_num < 50:  # Assume 2000s
            full_year = 2000 + year_num
        else:  # Assume 1900s (though unlikely for futures)
            full_year = 1900 + year_num
        
        month_num = self.month_codes[month_code]
        
        return month_num, full_year
    
    def get_contract_expiration_date(self, symbol):
        """Get expiration date for a contract"""
        if symbol in self.symbol_map:
            msg = self.symbol_map[symbol]
            if hasattr(msg, 'expiration') and msg.expiration:
                # Convert nanoseconds to datetime
                return pd.to_datetime(msg.expiration, unit='ns')
        return None
    
    def get_continuous_contract_mapping(self, asset, num_contracts=12):
        """Get mapping of continuous contracts (front month, 2nd month, etc.)"""
        if asset not in self.contract_chains:
            return {}
        
        chain = self.contract_chains[asset]
        current_time = pd.Timestamp.now()
        
        # Filter to active contracts (not expired)
        active_contracts = []
        for contract in chain:
            if contract['expiration']:
                exp_date = pd.to_datetime(contract['expiration'], unit='ns')
                if exp_date > current_time:
                    active_contracts.append(contract)
        
        # Create continuous mapping
        mapping = {}
        for i, contract in enumerate(active_contracts[:num_contracts]):
            if i == 0:
                label = "Front Month"
            elif i == 1:
                label = "2nd Month"
            elif i == 2:
                label = "3rd Month"
            else:
                label = f"{i+1}th Month"
            
            exp_date = pd.to_datetime(contract['expiration'], unit='ns')
            month, year = self.parse_contract_month(contract['symbol'])
            
            mapping[label] = {
                'symbol': contract['symbol'],
                'instrument_id': contract['instrument_id'],
                'expiration': exp_date,
                'month': month,
                'year': year,
                'month_name': self.month_names.get(month, 'Unknown'),
                'tick_size': contract['tick_size']
            }
        
        return mapping
    
    def get_quarterly_contracts(self, asset):
        """Get quarterly contracts (Mar, Jun, Sep, Dec)"""
        quarterly_months = [3, 6, 9, 12]  # H, M, U, Z
        
        if asset not in self.contract_chains:
            return {}
        
        quarterly_contracts = {}
        current_time = pd.Timestamp.now()
        
        for contract in self.contract_chains[asset]:
            if contract['expiration']:
                exp_date = pd.to_datetime(contract['expiration'], unit='ns')
                if exp_date > current_time:
                    month, year = self.parse_contract_month(contract['symbol'])
                    if month in quarterly_months:
                        quarter_name = {3: 'Q1', 6: 'Q2', 9: 'Q3', 12: 'Q4'}[month]
                        key = f"{year}-{quarter_name}"
                        
                        quarterly_contracts[key] = {
                            'symbol': contract['symbol'],
                            'instrument_id': contract['instrument_id'],
                            'expiration': exp_date,
                            'month': month,
                            'year': year,
                            'month_name': self.month_names[month],
                            'quarter': quarter_name,
                            'tick_size': contract['tick_size']
                        }
        
        return quarterly_contracts
    
    def find_contract_by_month_year(self, asset, month, year):
        """Find specific contract by month and year"""
        if asset not in self.contract_chains:
            return None
        
        for contract in self.contract_chains[asset]:
            contract_month, contract_year = self.parse_contract_month(contract['symbol'])
            if contract_month == month and contract_year == year:
                exp_date = pd.to_datetime(contract['expiration'], unit='ns') if contract['expiration'] else None
                return {
                    'symbol': contract['symbol'],
                    'instrument_id': contract['instrument_id'],
                    'expiration': exp_date,
                    'month': contract_month,
                    'year': contract_year,
                    'month_name': self.month_names.get(contract_month, 'Unknown'),
                    'tick_size': contract['tick_size']
                }
        
        return None
    
    def get_roll_calendar(self, asset, months_ahead=12):
        """Get roll calendar showing when contracts expire"""
        if asset not in self.contract_chains:
            return []
        
        roll_calendar = []
        current_time = pd.Timestamp.now()
        
        for contract in self.contract_chains[asset]:
            if contract['expiration']:
                exp_date = pd.to_datetime(contract['expiration'], unit='ns')
                if exp_date > current_time:
                    month, year = self.parse_contract_month(contract['symbol'])
                    days_to_expiry = (exp_date - current_time).days
                    
                    if days_to_expiry <= months_ahead * 30:  # Rough filter
                        roll_calendar.append({
                            'symbol': contract['symbol'],
                            'expiration': exp_date,
                            'days_to_expiry': days_to_expiry,
                            'month': month,
                            'year': year,
                            'month_name': self.month_names.get(month, 'Unknown')
                        })
        
        # Sort by expiration
        roll_calendar.sort(key=lambda x: x['expiration'])
        return roll_calendar
    
    def export_contract_mappings(self, asset, filename=None):
        """Export contract mappings to CSV"""
        if asset not in self.contract_chains:
            print(f"❌ No contracts found for asset {asset}")
            return
        
        # Prepare data for export
        export_data = []
        for contract in self.contract_chains[asset]:
            month, year = self.parse_contract_month(contract['symbol'])
            exp_date = pd.to_datetime(contract['expiration'], unit='ns') if contract['expiration'] else None
            
            export_data.append({
                'symbol': contract['symbol'],
                'instrument_id': contract['instrument_id'],
                'asset': asset,
                'month_code': self.code_to_month.get(month, ''),
                'month_number': month,
                'month_name': self.month_names.get(month, 'Unknown'),
                'year': year,
                'expiration_date': exp_date,
                'tick_size': contract['tick_size'],
                'days_to_expiry': (exp_date - pd.Timestamp.now()).days if exp_date else None
            })
        
        df = pd.DataFrame(export_data)
        
        if not filename:
            filename = f"{asset.lower()}_contract_mappings.csv"
        
        filepath = os.path.join(os.path.dirname(__file__), filename)
        df.to_csv(filepath, index=False)
        print(f"✅ Exported {len(df)} {asset} contracts to {filepath}")
        
        return df

def demonstrate_definition_usage():
    """Demonstrate how to use definition schema for contract mapping"""
    print("🚀 DEFINITION SCHEMA USAGE DEMONSTRATION")
    print("="*60)
    
    # Initialize mapper
    mapper = DefinitionSchemaMapper()
    
    # Load ES definitions
    if not mapper.load_definitions(asset_filter="ES"):
        return
    
    print(f"\n📊 ES CONTRACT ANALYSIS:")
    print("-" * 50)
    
    # Show continuous contract mapping
    continuous = mapper.get_continuous_contract_mapping("ES", num_contracts=6)
    print(f"\n🔄 CONTINUOUS CONTRACT MAPPING:")
    for label, contract in continuous.items():
        print(f"   {label:>12}: {contract['symbol']:>8} | "
              f"{contract['month_name']} {contract['year']} | "
              f"Expires: {contract['expiration'].strftime('%Y-%m-%d')}")
    
    # Show quarterly contracts
    quarterly = mapper.get_quarterly_contracts("ES")
    print(f"\n📅 QUARTERLY CONTRACTS (Next 8):")
    for key, contract in list(quarterly.items())[:8]:
        print(f"   {key:>8}: {contract['symbol']:>8} | "
              f"{contract['month_name']} {contract['year']} | "
              f"Expires: {contract['expiration'].strftime('%Y-%m-%d')}")
    
    # Show roll calendar
    roll_calendar = mapper.get_roll_calendar("ES", months_ahead=6)
    print(f"\n📆 ROLL CALENDAR (Next 6 months):")
    for roll in roll_calendar[:10]:
        print(f"   {roll['symbol']:>8}: {roll['days_to_expiry']:>3} days | "
              f"{roll['month_name']} {roll['year']} | "
              f"{roll['expiration'].strftime('%Y-%m-%d')}")
    
    # Demonstrate specific lookups
    print(f"\n🔍 SPECIFIC CONTRACT LOOKUPS:")
    
    # Find March 2025 contract
    march_2025 = mapper.find_contract_by_month_year("ES", 3, 2025)
    if march_2025:
        print(f"   March 2025: {march_2025['symbol']} (ID: {march_2025['instrument_id']})")
    
    # Find June 2025 contract
    june_2025 = mapper.find_contract_by_month_year("ES", 6, 2025)
    if june_2025:
        print(f"   June 2025:  {june_2025['symbol']} (ID: {june_2025['instrument_id']})")
    
    # Export mappings
    print(f"\n📁 EXPORTING CONTRACT MAPPINGS:")
    df = mapper.export_contract_mappings("ES")
    
    print(f"\n🎯 PRACTICAL USAGE EXAMPLES:")
    print("-" * 50)
    print(f"✅ Map continuous contracts to specific months")
    print(f"✅ Build roll calendars for strategy timing")
    print(f"✅ Cross-reference symbol → instrument_id → month")
    print(f"✅ Handle contract expirations and rollovers")
    print(f"✅ Filter quarterly vs monthly contracts")
    
    return mapper

if __name__ == "__main__":
    demonstrate_definition_usage() 