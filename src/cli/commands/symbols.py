"""
Symbol Commands Module

This module contains symbol management CLI commands including group management,
symbol discovery, advanced lookup, and exchange mapping analysis.
"""

import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from dotenv import load_dotenv

# Initialize Rich console early
console = Console()

try:
    from utils.custom_logger import setup_logging, get_logger, log_status, log_progress, log_user_message
    from cli.symbol_groups import SymbolGroupManager
    from cli.enhanced_help_utils import SymbolHelper
    from cli.smart_validation import create_smart_validator
    from cli.exchange_mapping import get_exchange_mapper
except ImportError as e:
    # Graceful degradation for missing dependencies
    console.print(f"⚠️  [yellow]Import warning: {e}[/yellow]")
    
    # Create mock implementations for essential classes
    class MockLogger:
        def exception(self, msg): pass
        def info(self, msg): pass
        def warning(self, msg): pass
    
    def get_logger(name): return MockLogger()
    def log_user_message(msg): pass
    def log_status(msg): pass
    def log_progress(msg): pass
    
    class MockSymbolGroupManager:
        def list_groups(self, category=None):
            return {"SP500_SAMPLE": {"category": "Equity", "symbols": ["ES.c.0", "SPY"], "description": "S&P 500 sample"}}
        def get_group_info(self, name):
            return {"name": name, "symbols": ["ES.c.0"], "description": "Mock group"}
        def create_group(self, name, symbols, description=""):
            return True
        def delete_group(self, name):
            return True
    
    class MockSymbolHelper:
        def show_symbols(self, category=None, search=None):
            console.print("📈 [green]Mock symbols: ES.c.0, NQ.c.0, CL.c.0[/green]")
    
    class MockSmartValidator:
        def validate_symbol(self, symbol):
            return type('ValidationResult', (), {
                'is_valid': True, 
                'suggestions': [{'symbol': 'ES.c.0', 'asset_class': 'Future', 'sector': 'Index'}]
            })()
    
    def create_smart_validator():
        return MockSmartValidator()
    
    class MockExchangeMapper:
        def map_symbol_to_exchange(self, symbol, fallback="NYSE"):
            return "CME_Equity", 0.95, type('MockMapping', (), {
                'asset_class': type('AssetClass', (), {'value': 'futures'})(),
                'region': type('Region', (), {'value': 'us'})(),
                'description': 'Mock futures mapping'
            })()
        def map_symbols_to_exchange(self, symbols, fallback="NYSE"):
            return "CME_Equity", 0.95, {}
        def get_exchange_info(self, exchange):
            return {"name": exchange, "description": f"{exchange} Exchange", "trading_hours": "09:30-16:00"}
    
    def get_exchange_mapper():
        return MockExchangeMapper()
    
    # Assign mocks to expected globals
    SymbolGroupManager = MockSymbolGroupManager
    SymbolHelper = MockSymbolHelper

# Initialize logging
logger = get_logger(__name__)

# Create Typer app for symbol commands
app = typer.Typer(
    name="symbols",
    help="Symbol management commands (groups, symbols, symbol-lookup, exchange-mapping)",
    no_args_is_help=False
)


@app.command()
def groups(
    list_all: bool = typer.Option(
        False,
        "--list", "-l",
        help="List all available symbol groups"
    ),
    category: Optional[str] = typer.Option(
        None,
        "--category", "-c",
        help="Filter by category (Equity, Futures, Energy, etc.)"
    ),
    info: Optional[str] = typer.Option(
        None,
        "--info", "-i",
        help="Show detailed info for a specific group"
    ),
    create: Optional[str] = typer.Option(
        None,
        "--create",
        help="Create a new custom group"
    ),
    symbols: Optional[str] = typer.Option(
        None,
        "--symbols",
        help="Symbols for new group (comma-separated)"
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        help="Description for new group"
    ),
    delete: Optional[str] = typer.Option(
        None,
        "--delete",
        help="Delete a custom group"
    )
):
    """
    🔗 Manage symbol groups for batch operations.
    
    Create, list, and manage symbol groups for efficient batch processing.
    Supports both predefined groups (SP500_SAMPLE, DOW30) and custom groups.
    
    Examples:
        python main.py groups --list                           # List all groups
        python main.py groups --category Equity                # Filter by category
        python main.py groups --info SP500_SAMPLE              # Show group details
        python main.py groups --create MY_GROUP --symbols "ES.c.0,NQ.c.0" --description "My futures"
        python main.py groups --delete MY_GROUP                # Delete custom group
    """
    log_user_message(f"Symbol groups command: list={list_all}, category={category}, info={info}, create={create}")
    
    try:
        manager = SymbolGroupManager()
        
        if delete:
            console.print(f"🗑️  [yellow]Deleting group: {delete}[/yellow]")
            if manager.delete_group(delete):
                console.print(f"✅ [green]Group '{delete}' deleted successfully[/green]")
            else:
                console.print(f"❌ [red]Failed to delete group '{delete}'[/red]")
                console.print("💡 [blue]Only custom groups can be deleted[/blue]")
                raise typer.Exit(1)
        
        elif create:
            if not symbols:
                console.print("❌ [red]--symbols required when creating a group[/red]")
                raise typer.Exit(1)
            
            symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
            if not symbol_list:
                console.print("❌ [red]No valid symbols provided[/red]")
                raise typer.Exit(1)
            
            console.print(f"🔨 [cyan]Creating group: {create}[/cyan]")
            console.print(f"📊 Symbols: {', '.join(symbol_list)}")
            
            if manager.create_group(create, symbol_list, description or ""):
                console.print(f"✅ [green]Group '{create}' created successfully[/green]")
                console.print(f"📝 Contains {len(symbol_list)} symbols")
            else:
                console.print(f"❌ [red]Failed to create group '{create}'[/red]")
                raise typer.Exit(1)
        
        elif info:
            console.print(f"ℹ️  [bold cyan]Group Information: {info}[/bold cyan]")
            group_info = manager.get_group_info(info)
            
            if not group_info:
                console.print(f"❌ [red]Group '{info}' not found[/red]")
                console.print("💡 [blue]Use --list to see available groups[/blue]")
                raise typer.Exit(1)
            
            # Display group details
            table = Table(title=f"Group: {info}")
            table.add_column("Property", style="bold blue")
            table.add_column("Value", style="green")
            
            table.add_row("Name", group_info.get("name", info))
            table.add_row("Category", group_info.get("category", "N/A"))
            table.add_row("Description", group_info.get("description", "N/A"))
            table.add_row("Symbol Count", str(len(group_info.get("symbols", []))))
            
            console.print(table)
            
            # Display symbols
            symbols_list = group_info.get("symbols", [])
            if symbols_list:
                console.print(f"\n📊 [bold cyan]Symbols ({len(symbols_list)})[/bold cyan]")
                for i, symbol in enumerate(symbols_list, 1):
                    console.print(f"  {i:2d}. {symbol}")
        
        else:
            # List groups (default behavior)
            console.print("🔗 [bold cyan]Available Symbol Groups[/bold cyan]\n")
            
            groups_dict = manager.list_groups(category=category)
            if not groups_dict:
                console.print("📝 [yellow]No groups found[/yellow]")
                if category:
                    console.print(f"💡 [blue]No groups found for category: {category}[/blue]")
                return
            
            # Create groups table
            table = Table(title="Symbol Groups")
            table.add_column("Group Name", style="bold blue")
            table.add_column("Category", style="cyan")
            table.add_column("Symbols", style="green", justify="right")
            table.add_column("Description", style="dim")
            
            for group_name, group_data in groups_dict.items():
                # Handle both dict and list structures for compatibility
                if isinstance(group_data, dict):
                    symbol_count = len(group_data.get("symbols", []))
                    category = group_data.get("category", "Custom")
                    description = group_data.get("description", "")
                else:
                    # Handle list structure (legacy format)
                    symbol_count = len(group_data) if isinstance(group_data, list) else 0
                    category = "Custom"
                    description = "Symbol group"
                
                table.add_row(
                    group_name,
                    category,
                    str(symbol_count),
                    description[:50] + ("..." if len(description) > 50 else "")
                )
            
            console.print(table)
            console.print(f"\n💡 [blue]Use --info GROUP_NAME for detailed information[/blue]")
            
        log_status("Symbol groups command completed successfully")
    
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"❌ [red]Groups command error: {e}[/red]")
        console.print(f"💡 [blue]Use 'python main.py troubleshoot groups' for help[/blue]")
        logger.exception("Groups command failed")
        raise typer.Exit(1)


@app.command()
def symbols(
    category: Optional[str] = typer.Option(
        None,
        "--category", "-c",
        help="Filter by category like 'Energy', 'Metals', 'Currencies'"
    ),
    search: Optional[str] = typer.Option(
        None,
        "--search", "-s",
        help="Search for symbols by name or code"
    )
):
    """
    📈 Symbol discovery and reference tool.
    
    Browse and search available symbols by category or search pattern.
    Provides organized symbol browsing for market data exploration.
    
    Examples:
        python main.py symbols                              # Show all symbols
        python main.py symbols --category Energy           # Energy sector symbols
        python main.py symbols --search "crude oil"        # Search by name
        python main.py symbols --search "CL"               # Search by symbol pattern
    """
    log_user_message(f"Symbols discovery: category={category}, search={search}")
    console.print("📈 [bold cyan]Symbol Discovery[/bold cyan]\n")
    
    try:
        helper = SymbolHelper()
        
        if category:
            console.print(f"🔍 [cyan]Showing symbols for category: {category}[/cyan]")
        elif search:
            console.print(f"🔍 [cyan]Searching symbols for: {search}[/cyan]")
        else:
            console.print("📊 [cyan]Showing all available symbols[/cyan]")
        
        # Delegate to SymbolHelper for the actual display
        helper.show_symbols(category=category, search=search)
        
        console.print(f"\n💡 [blue]Use 'python main.py symbol-lookup SYMBOL' for detailed symbol information[/blue]")
        log_status("Symbol discovery completed successfully")
    
    except Exception as e:
        console.print(f"❌ [red]Symbols discovery error: {e}[/red]")
        console.print(f"💡 [blue]Use 'python main.py troubleshoot symbols' for help[/blue]")
        logger.exception("Symbols discovery command failed")
        raise typer.Exit(1)


@app.command("symbol-lookup")
def symbol_lookup(
    symbol: str = typer.Argument(..., help="Symbol to look up"),
    fuzzy: bool = typer.Option(
        False,
        "--fuzzy", "-f",
        help="Enable fuzzy search for similar symbols"
    ),
    suggestions: int = typer.Option(
        5,
        "--suggestions", "-s",
        help="Number of suggestions to show (default: 5)"
    )
):
    """
    🔍 Advanced symbol lookup with autocomplete and suggestions.
    
    Performs intelligent symbol validation and lookup with fuzzy matching
    and detailed symbol information including asset class and sector data.
    
    Examples:
        python main.py symbol-lookup ES.c.0                 # Exact lookup
        python main.py symbol-lookup "ES" --fuzzy           # Fuzzy search
        python main.py symbol-lookup "crude" --fuzzy --suggestions 10  # More suggestions
    """
    log_user_message(f"Symbol lookup: {symbol}, fuzzy={fuzzy}, suggestions={suggestions}")
    console.print(f"🔍 [bold cyan]Symbol Lookup: {symbol}[/bold cyan]\n")
    
    try:
        validator = create_smart_validator()
        result = validator.validate_symbol(symbol)
        
        if result.is_valid:
            console.print(f"✅ [green]Symbol '{symbol}' is valid[/green]")
            
            # If we have metadata, show detailed information
            if hasattr(result, 'metadata') and result.metadata:
                console.print(f"\n📊 [bold cyan]Symbol Details[/bold cyan]")
                
                table = Table(title=f"Symbol Information: {symbol}")
                table.add_column("Property", style="bold blue")
                table.add_column("Value", style="green")
                
                metadata = result.metadata
                table.add_row("Symbol", symbol)
                table.add_row("Asset Class", metadata.get("asset_class", "N/A"))
                table.add_row("Sector", metadata.get("sector", "N/A"))
                table.add_row("Trading Status", metadata.get("trading_status", "N/A"))
                table.add_row("Exchange", metadata.get("exchange", "N/A"))
                
                console.print(table)
        
        else:
            console.print(f"❌ [red]Symbol '{symbol}' not found[/red]")
            
            if fuzzy and hasattr(result, 'suggestions') and result.suggestions:
                console.print(f"\n💡 [yellow]Similar symbols found:[/yellow]")
                
                # Create suggestions table
                suggestions_table = Table(title="Symbol Suggestions")
                suggestions_table.add_column("Symbol", style="bold blue")
                suggestions_table.add_column("Asset Class", style="cyan")
                suggestions_table.add_column("Sector", style="green")
                
                for suggestion in result.suggestions[:suggestions]:
                    suggestions_table.add_row(
                        suggestion.get("symbol", "N/A"),
                        suggestion.get("asset_class", "N/A"),
                        suggestion.get("sector", "N/A")
                    )
                
                console.print(suggestions_table)
                console.print(f"\n💡 [blue]Use exact symbol for detailed lookup[/blue]")
            
            elif fuzzy:
                console.print(f"💡 [blue]No similar symbols found. Try a different search pattern.[/blue]")
            else:
                console.print(f"💡 [blue]Use --fuzzy for similar symbol suggestions[/blue]")
        
        log_status("Symbol lookup completed successfully")
    
    except Exception as e:
        console.print(f"❌ [red]Symbol lookup error: {e}[/red]")
        console.print(f"💡 [blue]Use 'python main.py troubleshoot symbol-lookup' for help[/blue]")
        logger.exception("Symbol lookup command failed")
        raise typer.Exit(1)


@app.command("exchange-mapping")
def exchange_mapping(
    symbols: Optional[str] = typer.Argument(
        None,
        help="Comma-separated symbols to analyze"
    ),
    list_exchanges: bool = typer.Option(
        False,
        "--list",
        help="List all supported exchanges"
    ),
    mappings: bool = typer.Option(
        False,
        "--mappings",
        help="Show all mapping rules"
    ),
    info: Optional[str] = typer.Option(
        None,
        "--info",
        help="Get detailed info about specific exchange"
    ),
    test: Optional[str] = typer.Option(
        None,
        "--test",
        help="Test mapping for single symbol"
    ),
    min_confidence: float = typer.Option(
        0.0,
        "--min-confidence",
        help="Minimum confidence threshold for results (0.0-1.0)"
    )
):
    """
    🏢 Intelligent symbol-to-exchange mapping analysis and testing.
    
    Analyzes symbols to determine their most likely exchanges using pattern
    matching and confidence scoring. Supports batch analysis and validation.
    
    Examples:
        python main.py exchange-mapping --list              # List exchanges
        python main.py exchange-mapping --mappings          # Show mapping rules
        python main.py exchange-mapping --info NYSE         # Exchange details
        python main.py exchange-mapping --test ES.c.0       # Test single symbol
        python main.py exchange-mapping "ES.c.0,NQ.c.0" --min-confidence 0.8  # Batch analysis
    """
    log_user_message(f"Exchange mapping: symbols={symbols}, list={list_exchanges}, test={test}")
    
    try:
        mapper = get_exchange_mapper()
        
        if list_exchanges:
            console.print("🏢 [bold cyan]Supported Exchange Calendars[/bold cyan]\n")
            
            # Get exchanges from the predefined exchange info in mapper
            exchanges = ["NYSE", "NASDAQ", "CME_Equity", "CME_Energy", "CME_Commodity", "CME_FX", "CME_InterestRate", "LSE", "XETR"]
            table = Table(title="Exchange Calendars")
            table.add_column("Exchange", style="bold blue")
            table.add_column("Full Name", style="green")
            table.add_column("Market Hours", style="cyan")
            
            for exchange in exchanges:
                exchange_data = mapper.get_exchange_info(exchange)
                name = exchange_data.get("name", exchange)
                hours = exchange_data.get("trading_hours", "Various")
                table.add_row(exchange, name, hours)
            
            console.print(table)
            console.print(f"\n💡 [blue]Use --info EXCHANGE for detailed information[/blue]")
        
        elif mappings:
            console.print("🗺️  [bold cyan]Exchange Mapping Rules[/bold cyan]\n")
            
            # Show the mapping patterns by examining the ExchangeMapper mappings
            console.print("📋 [cyan]Pattern-based mapping rules:[/cyan]")
            
            # Display some example patterns from the actual mappings
            example_patterns = [
                "CL.FUT, NG.c.0, HO.H24 → CME_Energy (Energy futures)",
                "ES.FUT, NQ.c.0, RTY.H24 → CME_Equity (Equity index futures)",
                "GC.c.0, SI.H24, ZC.FUT → CME_Commodity (Agricultural & Metals)",
                "6E.FUT, 6J.c.0, 6B.H24 → CME_FX (Currency futures)",
                "SPY, IWM, DIA, XLF → NYSE (Major ETFs)",
                "AAPL, MSFT, GOOGL → NASDAQ (Tech stocks)",
                "VODL.L, BP.L → LSE (London Stock Exchange)",
                "SAP.DE, BMW.DE → XETR (Deutsche Börse)"
            ]
            
            for pattern in example_patterns:
                console.print(f"  • {pattern}")
            
            console.print(f"\n💡 [blue]Rules are applied with confidence scoring based on regex patterns[/blue]")
            console.print(f"💡 [blue]Use --test SYMBOL to see how a specific symbol maps[/blue]")
        
        elif info:
            console.print(f"ℹ️  [bold cyan]Exchange Information: {info}[/bold cyan]\n")
            
            exchange_data = mapper.get_exchange_info(info)
            if not exchange_data:
                console.print(f"❌ [red]Exchange '{info}' not found[/red]")
                console.print("💡 [blue]Use --list to see available exchanges[/blue]")
                raise typer.Exit(1)
            
            table = Table(title=f"Exchange: {info}")
            table.add_column("Property", style="bold blue")
            table.add_column("Value", style="green")
            
            table.add_row("Exchange Code", info)
            table.add_row("Full Name", exchange_data.get("name", "N/A"))
            table.add_row("Description", exchange_data.get("description", "N/A"))
            table.add_row("Calendar Type", exchange_data.get("calendar", "N/A"))
            
            console.print(table)
        
        elif test:
            console.print(f"🧪 [cyan]Testing symbol mapping: {test}[/cyan]")
            
            exchange, confidence, mapping_info = mapper.map_symbol_to_exchange(test)
            
            console.print(f"📊 [green]Mapping Result:[/green]")
            console.print(f"  Symbol: {test}")
            console.print(f"  Exchange: {exchange}")
            console.print(f"  Confidence: {confidence:.1%}")
            
            if mapping_info:
                console.print(f"  Asset Class: {mapping_info.asset_class.value}")
                console.print(f"  Region: {mapping_info.region.value}")
                console.print(f"  Description: {mapping_info.description}")
            
            if confidence < 0.5:
                console.print(f"⚠️  [yellow]Low confidence mapping[/yellow]")
            elif confidence >= 0.9:
                console.print(f"✅ [green]High confidence mapping[/green]")
        
        elif symbols:
            symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
            if not symbol_list:
                console.print("❌ [red]No valid symbols provided[/red]")
                raise typer.Exit(1)
            
            console.print(f"🏢 [bold cyan]Exchange Mapping Analysis[/bold cyan]")
            console.print(f"📊 Analyzing {len(symbol_list)} symbols\n")
            
            # Map each symbol individually to get detailed results
            results = []
            for symbol in symbol_list:
                exchange, confidence, mapping_info = mapper.map_symbol_to_exchange(symbol)
                results.append({
                    "symbol": symbol,
                    "exchange": exchange,
                    "confidence": confidence,
                    "mapping_info": mapping_info
                })
            
            # Filter by confidence threshold
            filtered_results = [r for r in results if r.get("confidence", 0) >= min_confidence]
            
            if not filtered_results:
                console.print(f"❌ [red]No results above confidence threshold {min_confidence:.1%}[/red]")
                console.print("💡 [blue]Try lowering --min-confidence[/blue]")
                raise typer.Exit(1)
            
            # Create results table
            table = Table(title="Symbol-Exchange Mapping Results")
            table.add_column("Symbol", style="bold blue")
            table.add_column("Exchange", style="green")
            table.add_column("Confidence", style="cyan", justify="right")
            table.add_column("Asset Class", style="magenta")
            
            for result in filtered_results:
                symbol = result.get("symbol", "N/A")
                exchange = result.get("exchange", "Unknown")
                confidence = result.get("confidence", 0.0)
                mapping_info = result.get("mapping_info")
                asset_class = mapping_info.asset_class.value if mapping_info else "N/A"
                
                table.add_row(symbol, exchange, f"{confidence:.1%}", asset_class)
            
            console.print(table)
            
            # Show exchange distribution
            exchange_counts = {}
            for result in filtered_results:
                exchange = result.get("exchange", "Unknown")
                exchange_counts[exchange] = exchange_counts.get(exchange, 0) + 1
            
            console.print(f"\n📈 [cyan]Exchange Distribution:[/cyan]")
            for exchange, count in exchange_counts.items():
                console.print(f"  • {exchange}: {count} symbols")
        
        else:
            console.print("🏢 [bold cyan]Exchange Mapping Tool[/bold cyan]\n")
            console.print("📝 Available actions:")
            console.print("  --list              List all supported exchanges")
            console.print("  --mappings          Show mapping rules")
            console.print("  --info EXCHANGE     Get exchange details")
            console.print("  --test SYMBOL       Test single symbol mapping")
            console.print("  SYMBOLS             Analyze symbol list")
            console.print("\n💡 [blue]Example: python main.py exchange-mapping 'ES.c.0,NQ.c.0'[/blue]")
        
        log_status("Exchange mapping completed successfully")
    
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"❌ [red]Exchange mapping error: {e}[/red]")
        console.print(f"💡 [blue]Use 'python main.py troubleshoot exchange-mapping' for help[/blue]")
        logger.exception("Exchange mapping command failed")
        raise typer.Exit(1)


# Export the app for module imports
__all__ = ["app", "groups", "symbols", "symbol_lookup", "exchange_mapping"]