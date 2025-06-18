"""
Symbol Group Manager for organizing and managing collections of financial symbols.

This module provides functionality to work with predefined symbol groups
(like SP500, DOW30) and custom user-defined groups for batch operations.
"""

import json
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import requests
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


@dataclass
class SymbolGroup:
    """Represents a collection of financial symbols."""
    name: str
    description: str
    symbols: List[str]
    category: str = "custom"
    created_at: Optional[str] = None
    last_updated: Optional[str] = None
    source: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.last_updated is None:
            self.last_updated = self.created_at


class SymbolGroupManager:
    """Manage predefined and custom symbol groups for batch operations."""
    
    # Predefined symbol groups with static definitions
    PREDEFINED_GROUPS = {
        'SP500_SAMPLE': {
            'description': 'Sample S&P 500 components (top 20 by market cap)',
            'category': 'equity_indices',
            'symbols': [
                'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'TSLA', 'GOOG', 'BRK.B',
                'UNH', 'XOM', 'META', 'JNJ', 'JPM', 'V', 'PG', 'HD', 'CVX', 'MA', 'ABBV', 'PFE'
            ]
        },
        'DOW30': {
            'description': 'Dow Jones Industrial Average 30 components',
            'category': 'equity_indices',
            'symbols': [
                'AAPL', 'AMGN', 'AXP', 'BA', 'CAT', 'CRM', 'CSCO', 'CVX', 'DIS', 'DOW',
                'GS', 'HD', 'HON', 'IBM', 'INTC', 'JNJ', 'JPM', 'KO', 'MCD', 'MMM',
                'MRK', 'MSFT', 'NKE', 'PG', 'TRV', 'UNH', 'V', 'VZ', 'WBA', 'WMT'
            ]
        },
        'NASDAQ100_SAMPLE': {
            'description': 'Sample NASDAQ 100 components (top 15)',
            'category': 'equity_indices',
            'symbols': [
                'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'TSLA', 'GOOG', 'META',
                'AVGO', 'COST', 'NFLX', 'AMD', 'PEP', 'ADBE', 'CMCSA'
            ]
        },
        'ENERGY_FUTURES': {
            'description': 'Major Energy Futures Contracts',
            'category': 'commodities',
            'symbols': ['CL.c.0', 'NG.c.0', 'RB.c.0', 'HO.c.0', 'XB.c.0']
        },
        'METALS_FUTURES': {
            'description': 'Precious and Base Metals Futures',
            'category': 'commodities',
            'symbols': ['GC.c.0', 'SI.c.0', 'HG.c.0', 'PA.c.0', 'PL.c.0']
        },
        'GRAINS_FUTURES': {
            'description': 'Agricultural Grains Futures',
            'category': 'commodities',
            'symbols': ['ZC.c.0', 'ZW.c.0', 'ZS.c.0', 'ZM.c.0', 'ZL.c.0', 'ZO.c.0']
        },
        'INDEX_FUTURES': {
            'description': 'Major Index Futures Contracts',
            'category': 'indices',
            'symbols': ['ES.c.0', 'NQ.c.0', 'RTY.c.0', 'YM.c.0', 'EMD.c.0']
        },
        'CURRENCY_FUTURES': {
            'description': 'Major Currency Futures',
            'category': 'forex',
            'symbols': ['6E.c.0', '6B.c.0', '6J.c.0', '6A.c.0', '6C.c.0', '6S.c.0']
        },
        'RATES_FUTURES': {
            'description': 'Interest Rate Futures',
            'category': 'rates',
            'symbols': ['ZB.c.0', 'ZN.c.0', 'ZF.c.0', 'ZT.c.0', 'UB.c.0']
        },
        'CRYPTO_SAMPLE': {
            'description': 'Sample Cryptocurrency symbols',
            'category': 'crypto',
            'symbols': ['BTC-USD', 'ETH-USD', 'ADA-USD', 'SOL-USD', 'MATIC-USD']
        }
    }
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize the symbol group manager.
        
        Args:
            cache_dir: Directory to store custom groups and cache
        """
        self.cache_dir = cache_dir or Path.home() / ".hdi_symbol_groups"
        self.cache_dir.mkdir(exist_ok=True)
        self.custom_groups_file = self.cache_dir / "custom_groups.json"
        self.custom_groups: Dict[str, SymbolGroup] = {}
        
        # Load custom groups
        self._load_custom_groups()
    
    def _load_custom_groups(self) -> None:
        """Load custom groups from disk."""
        if self.custom_groups_file.exists():
            try:
                with open(self.custom_groups_file, 'r') as f:
                    data = json.load(f)
                    
                for name, group_data in data.items():
                    self.custom_groups[name] = SymbolGroup(
                        name=name,
                        description=group_data['description'],
                        symbols=group_data['symbols'],
                        category=group_data.get('category', 'custom'),
                        created_at=group_data.get('created_at'),
                        last_updated=group_data.get('last_updated'),
                        source=group_data.get('source')
                    )
            except Exception as e:
                console.print(f"[yellow]Warning: Failed to load custom groups: {e}[/yellow]")
    
    def _save_custom_groups(self) -> None:
        """Save custom groups to disk."""
        try:
            data = {}
            for name, group in self.custom_groups.items():
                data[name] = {
                    'description': group.description,
                    'symbols': group.symbols,
                    'category': group.category,
                    'created_at': group.created_at,
                    'last_updated': group.last_updated,
                    'source': group.source
                }
                
            with open(self.custom_groups_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to save custom groups: {e}[/yellow]")
    
    def resolve_group(self, group_identifier: str) -> List[str]:
        """Resolve a group identifier to a list of symbols.
        
        Args:
            group_identifier: Can be:
                - Predefined group name (e.g., 'SP500_SAMPLE')
                - Custom group name
                - Comma-separated symbol list (e.g., 'AAPL,MSFT,GOOGL')
                - Single symbol
                
        Returns:
            List of symbols
            
        Raises:
            ValueError: If group is not found
        """
        # Check if it's a comma-separated list
        if ',' in group_identifier:
            return [s.strip().upper() for s in group_identifier.split(',')]
        
        # Check predefined groups (case insensitive)
        group_upper = group_identifier.upper()
        if group_upper in self.PREDEFINED_GROUPS:
            return self.PREDEFINED_GROUPS[group_upper]['symbols'].copy()
        
        # Check custom groups
        if group_identifier in self.custom_groups:
            return self.custom_groups[group_identifier].symbols.copy()
        
        # Check if it matches any group by partial name
        matches = self._find_partial_matches(group_identifier)
        if len(matches) == 1:
            return self.resolve_group(matches[0])
        elif len(matches) > 1:
            raise ValueError(f"Ambiguous group name '{group_identifier}'. Matches: {', '.join(matches)}")
        
        # Assume it's a single symbol
        return [group_identifier.upper()]
    
    def _find_partial_matches(self, partial_name: str) -> List[str]:
        """Find groups that partially match the given name."""
        partial_lower = partial_name.lower()
        matches = []
        
        # Check predefined groups
        for group_name in self.PREDEFINED_GROUPS.keys():
            if partial_lower in group_name.lower():
                matches.append(group_name)
        
        # Check custom groups
        for group_name in self.custom_groups.keys():
            if partial_lower in group_name.lower():
                matches.append(group_name)
                
        return matches
    
    def get_group_info(self, group_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a group.
        
        Args:
            group_name: Name of the group
            
        Returns:
            Group information dictionary or None if not found
        """
        group_upper = group_name.upper()
        
        # Check predefined groups
        if group_upper in self.PREDEFINED_GROUPS:
            group_data = self.PREDEFINED_GROUPS[group_upper].copy()
            group_data['name'] = group_upper
            group_data['type'] = 'predefined'
            group_data['symbol_count'] = len(group_data['symbols'])
            return group_data
        
        # Check custom groups
        if group_name in self.custom_groups:
            group = self.custom_groups[group_name]
            return {
                'name': group.name,
                'description': group.description,
                'symbols': group.symbols,
                'category': group.category,
                'type': 'custom',
                'symbol_count': len(group.symbols),
                'created_at': group.created_at,
                'last_updated': group.last_updated,
                'source': group.source
            }
        
        return None
    
    def list_groups(self, category: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """List all available groups.
        
        Args:
            category: Optional category filter
            
        Returns:
            Dictionary with 'predefined' and 'custom' group lists
        """
        result = {'predefined': [], 'custom': []}
        
        # Add predefined groups
        for name, data in self.PREDEFINED_GROUPS.items():
            if category is None or data.get('category') == category:
                group_info = data.copy()
                group_info['name'] = name
                group_info['type'] = 'predefined'
                group_info['symbol_count'] = len(group_info['symbols'])
                result['predefined'].append(group_info)
        
        # Add custom groups
        for group in self.custom_groups.values():
            if category is None or group.category == category:
                result['custom'].append({
                    'name': group.name,
                    'description': group.description,
                    'category': group.category,
                    'type': 'custom',
                    'symbol_count': len(group.symbols),
                    'created_at': group.created_at,
                    'last_updated': group.last_updated
                })
        
        return result
    
    def create_custom_group(self, name: str, symbols: List[str], 
                          description: str = "", category: str = "custom") -> None:
        """Create a new custom symbol group.
        
        Args:
            name: Group name
            symbols: List of symbols
            description: Group description
            category: Group category
        """
        # Validate symbols
        if not symbols:
            raise ValueError("Symbol list cannot be empty")
        
        # Clean and validate symbol names
        cleaned_symbols = []
        for symbol in symbols:
            cleaned = symbol.strip().upper()
            if cleaned:
                cleaned_symbols.append(cleaned)
        
        if not cleaned_symbols:
            raise ValueError("No valid symbols provided")
        
        # Create group
        group = SymbolGroup(
            name=name,
            description=description or f"Custom group with {len(cleaned_symbols)} symbols",
            symbols=cleaned_symbols,
            category=category
        )
        
        self.custom_groups[name] = group
        self._save_custom_groups()
        
        console.print(f"✅ Created custom group '{name}' with {len(cleaned_symbols)} symbols")
    
    def delete_custom_group(self, name: str) -> None:
        """Delete a custom group.
        
        Args:
            name: Group name to delete
            
        Raises:
            ValueError: If group doesn't exist or is predefined
        """
        if name.upper() in self.PREDEFINED_GROUPS:
            raise ValueError("Cannot delete predefined groups")
        
        if name not in self.custom_groups:
            raise ValueError(f"Custom group '{name}' not found")
        
        del self.custom_groups[name]
        self._save_custom_groups()
        
        console.print(f"✅ Deleted custom group '{name}'")
    
    def display_group_table(self, groups: Optional[List[str]] = None) -> None:
        """Display groups in a formatted table.
        
        Args:
            groups: Optional list of specific groups to display
        """
        all_groups = self.list_groups()
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Category", style="yellow")
        table.add_column("Symbols", justify="right", style="blue")
        table.add_column("Description", style="dim")
        
        # Add predefined groups
        for group in all_groups['predefined']:
            if groups is None or group['name'] in groups:
                table.add_row(
                    group['name'],
                    "Predefined",
                    group.get('category', 'N/A'),
                    str(group['symbol_count']),
                    group.get('description', 'N/A')
                )
        
        # Add custom groups
        for group in all_groups['custom']:
            if groups is None or group['name'] in groups:
                table.add_row(
                    group['name'],
                    "Custom",
                    group.get('category', 'custom'),
                    str(group['symbol_count']),
                    group.get('description', 'N/A')
                )
        
        console.print("\n📊 [bold blue]Available Symbol Groups:[/bold blue]")
        console.print(table)
    
    def get_categories(self) -> Set[str]:
        """Get all available categories."""
        categories = set()
        
        # From predefined groups
        for group_data in self.PREDEFINED_GROUPS.values():
            categories.add(group_data.get('category', 'other'))
        
        # From custom groups
        for group in self.custom_groups.values():
            categories.add(group.category)
        
        return categories
    
    def validate_symbols(self, symbols: List[str]) -> Dict[str, Any]:
        """Validate a list of symbols and provide statistics.
        
        Args:
            symbols: List of symbols to validate
            
        Returns:
            Validation results with statistics
        """
        # Basic validation
        valid_symbols = []
        invalid_symbols = []
        
        for symbol in symbols:
            cleaned = symbol.strip().upper()
            if cleaned and len(cleaned) <= 20:  # Basic length check
                valid_symbols.append(cleaned)
            else:
                invalid_symbols.append(symbol)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_symbols = []
        for symbol in valid_symbols:
            if symbol not in seen:
                seen.add(symbol)
                unique_symbols.append(symbol)
        
        duplicates = len(valid_symbols) - len(unique_symbols)
        
        return {
            'total_input': len(symbols),
            'valid_symbols': unique_symbols,
            'invalid_symbols': invalid_symbols,
            'duplicates_removed': duplicates,
            'final_count': len(unique_symbols)
        }