"""
Smart validation system for CLI inputs with autocomplete and intelligent suggestions.

Provides comprehensive validation for symbols, dates, schemas, and other CLI parameters
with helpful error messages, autocomplete capabilities, and market calendar awareness.
"""

import re
import json
from typing import Dict, List, Tuple, Optional, Any, Set, Union
from datetime import datetime, date, timedelta
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import difflib
from functools import lru_cache

from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()


class ValidationLevel(Enum):
    """Validation severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    level: ValidationLevel
    message: str
    suggestions: List[str] = None
    corrected_value: str = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []
        if self.metadata is None:
            self.metadata = {}


class SymbolCache:
    """Cache for symbol lookups with fuzzy matching and suggestions."""
    
    def __init__(self, cache_file: Optional[Path] = None):
        """Initialize symbol cache.
        
        Args:
            cache_file: Optional file to persist symbol data
        """
        self.cache_file = cache_file or Path.home() / ".hdi_symbol_cache.json"
        self.symbols: Set[str] = set()
        self.symbol_metadata: Dict[str, Dict[str, Any]] = {}
        self.fuzzy_threshold = 0.6
        
        # Load existing cache
        self._load_cache()
        
        # Initialize with common symbols if cache is empty
        if not self.symbols:
            self._initialize_default_symbols()
            
    def _load_cache(self):
        """Load symbol cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    self.symbols = set(data.get('symbols', []))
                    self.symbol_metadata = data.get('metadata', {})
            except Exception:
                # If loading fails, start fresh
                pass
                
    def _save_cache(self):
        """Save symbol cache to disk."""
        try:
            data = {
                'symbols': list(self.symbols),
                'metadata': self.symbol_metadata,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            # Don't fail if we can't save cache
            pass
            
    def _initialize_default_symbols(self):
        """Initialize with common trading symbols."""
        # Major index futures
        index_futures = [
            "ES.c.0", "NQ.c.0", "RTY.c.0", "YM.c.0", "EMD.c.0"
        ]
        
        # Energy futures
        energy_futures = [
            "CL.c.0", "NG.c.0", "RB.c.0", "HO.c.0", "XB.c.0"
        ]
        
        # Metals futures
        metals_futures = [
            "GC.c.0", "SI.c.0", "HG.c.0", "PA.c.0", "PL.c.0"
        ]
        
        # Agricultural futures
        agricultural_futures = [
            "ZC.c.0", "ZW.c.0", "ZS.c.0", "ZM.c.0", "ZL.c.0"
        ]
        
        # Major stocks
        major_stocks = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "BRK.A",
            "JNJ", "V", "WMT", "PG", "JPM", "UNH", "DIS", "HD", "BAC", "MA",
            "PFE", "KO", "ADBE", "CRM", "NFLX", "INTC", "AMD", "ORCL"
        ]
        
        all_symbols = index_futures + energy_futures + metals_futures + agricultural_futures + major_stocks
        
        for symbol in all_symbols:
            self.add_symbol(symbol, self._get_symbol_metadata(symbol))
            
    def _get_symbol_metadata(self, symbol: str) -> Dict[str, Any]:
        """Get metadata for a symbol based on patterns."""
        metadata = {"symbol": symbol}
        
        if ".c.0" in symbol:
            metadata["type"] = "continuous_future"
            metadata["asset_class"] = "futures"
        elif symbol in ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA"]:
            metadata["type"] = "equity"
            metadata["asset_class"] = "stocks"
            metadata["sector"] = "technology"
        elif symbol in ["ES.c.0", "NQ.c.0", "RTY.c.0", "YM.c.0"]:
            metadata["asset_class"] = "index_futures"
            metadata["sector"] = "equity_indices"
        elif symbol in ["CL.c.0", "NG.c.0", "RB.c.0", "HO.c.0"]:
            metadata["asset_class"] = "energy_futures"
            metadata["sector"] = "commodities"
        elif symbol in ["GC.c.0", "SI.c.0", "HG.c.0", "PA.c.0", "PL.c.0"]:
            metadata["asset_class"] = "metals_futures"
            metadata["sector"] = "commodities"
            
        return metadata
        
    def add_symbol(self, symbol: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a symbol to the cache.
        
        Args:
            symbol: Symbol to add
            metadata: Optional metadata for the symbol
        """
        self.symbols.add(symbol.upper())
        if metadata:
            self.symbol_metadata[symbol.upper()] = metadata
        self._save_cache()
        
    def is_valid_symbol(self, symbol: str) -> bool:
        """Check if a symbol exists in the cache.
        
        Args:
            symbol: Symbol to check
            
        Returns:
            True if symbol exists
        """
        return symbol.upper() in self.symbols
        
    def fuzzy_search(self, symbol_input: str, limit: int = 5) -> List[Tuple[str, float]]:
        """Perform fuzzy search for symbol suggestions.
        
        Args:
            symbol_input: Input symbol to search for
            limit: Maximum number of suggestions
            
        Returns:
            List of (symbol, similarity_score) tuples
        """
        if not symbol_input:
            return []
            
        symbol_input = symbol_input.upper()
        suggestions = []
        
        # Check for exact prefix matches first
        prefix_matches = [s for s in self.symbols if s.startswith(symbol_input)]
        for match in prefix_matches[:limit]:
            suggestions.append((match, 1.0))
            
        # If we have enough prefix matches, return them
        if len(suggestions) >= limit:
            return suggestions[:limit]
            
        # Otherwise, use fuzzy matching
        remaining_limit = limit - len(suggestions)
        fuzzy_matches = difflib.get_close_matches(
            symbol_input, 
            self.symbols, 
            n=remaining_limit * 2,  # Get extra to filter by threshold
            cutoff=self.fuzzy_threshold
        )
        
        for match in fuzzy_matches:
            if match not in [s[0] for s in suggestions]:  # Avoid duplicates
                similarity = difflib.SequenceMatcher(None, symbol_input, match).ratio()
                suggestions.append((match, similarity))
                
        # Sort by similarity score (descending) and return top results
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions[:limit]
        
    def get_symbols_by_category(self, category: str) -> List[str]:
        """Get symbols by asset class or sector.
        
        Args:
            category: Category to filter by
            
        Returns:
            List of symbols in the category
        """
        matching_symbols = []
        for symbol, metadata in self.symbol_metadata.items():
            if (metadata.get('asset_class') == category or 
                metadata.get('sector') == category or
                metadata.get('type') == category):
                matching_symbols.append(symbol)
                
        return sorted(matching_symbols)
        
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a symbol.
        
        Args:
            symbol: Symbol to get info for
            
        Returns:
            Symbol metadata or None if not found
        """
        return self.symbol_metadata.get(symbol.upper())


class MarketCalendar:
    """Market calendar for date validation and trading day calculations."""
    
    def __init__(self):
        """Initialize market calendar."""
        self.known_holidays = self._get_known_holidays()
        
    def _get_known_holidays(self) -> Set[date]:
        """Get known market holidays.
        
        Returns:
            Set of holiday dates
        """
        # For demo purposes, include some common holidays
        # In production, this would integrate with a proper market calendar service
        holidays = set()
        
        current_year = datetime.now().year
        for year in range(current_year - 1, current_year + 2):
            # New Year's Day
            holidays.add(date(year, 1, 1))
            
            # Independence Day
            holidays.add(date(year, 7, 4))
            
            # Christmas
            holidays.add(date(year, 12, 25))
            
            # Thanksgiving (4th Thursday of November)
            thanksgiving = self._get_nth_weekday(year, 11, 3, 4)  # 4th Thursday
            holidays.add(thanksgiving)
            
        return holidays
        
    def _get_nth_weekday(self, year: int, month: int, weekday: int, n: int) -> date:
        """Get the nth occurrence of a weekday in a month.
        
        Args:
            year: Year
            month: Month
            weekday: Weekday (0=Monday, 6=Sunday)
            n: Which occurrence (1=first, 2=second, etc.)
            
        Returns:
            Date of the nth weekday
        """
        first_day = date(year, month, 1)
        first_weekday = first_day.weekday()
        
        # Calculate days to add to get to the first occurrence of the target weekday
        days_to_add = (weekday - first_weekday) % 7
        first_occurrence = first_day + timedelta(days=days_to_add)
        
        # Add weeks to get to the nth occurrence
        nth_occurrence = first_occurrence + timedelta(weeks=n-1)
        
        return nth_occurrence
        
    def is_trading_day(self, check_date: date) -> bool:
        """Check if a date is a trading day.
        
        Args:
            check_date: Date to check
            
        Returns:
            True if it's a trading day
        """
        # Weekend check
        if check_date.weekday() >= 5:  # Saturday or Sunday
            return False
            
        # Holiday check
        if check_date in self.known_holidays:
            return False
            
        return True
        
    def get_trading_days(self, start_date: date, end_date: date, symbol: str = None) -> List[date]:
        """Get all trading days in a date range.
        
        Args:
            start_date: Start date
            end_date: End date  
            symbol: Optional symbol for asset-specific calendars
            
        Returns:
            List of trading days
        """
        trading_days = []
        current_date = start_date
        
        while current_date <= end_date:
            if self.is_trading_day(current_date):
                trading_days.append(current_date)
            current_date += timedelta(days=1)
            
        return trading_days
        
    def get_next_trading_day(self, from_date: date) -> date:
        """Get the next trading day after a given date.
        
        Args:
            from_date: Starting date
            
        Returns:
            Next trading day
        """
        next_date = from_date + timedelta(days=1)
        while not self.is_trading_day(next_date):
            next_date += timedelta(days=1)
        return next_date
        
    def get_previous_trading_day(self, from_date: date) -> date:
        """Get the previous trading day before a given date.
        
        Args:
            from_date: Starting date
            
        Returns:
            Previous trading day
        """
        prev_date = from_date - timedelta(days=1)
        while not self.is_trading_day(prev_date):
            prev_date -= timedelta(days=1)
        return prev_date


class SmartValidator:
    """Intelligent input validation with suggestions and autocomplete."""
    
    def __init__(self, symbol_cache: Optional[SymbolCache] = None, 
                 market_calendar: Optional[MarketCalendar] = None):
        """Initialize smart validator.
        
        Args:
            symbol_cache: Optional symbol cache instance
            market_calendar: Optional market calendar instance
        """
        self.symbol_cache = symbol_cache or SymbolCache()
        self.market_calendar = market_calendar or MarketCalendar()
        
        # Common validation patterns
        self.date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
            r'^\d{1,2}/\d{1,2}/\d{4}$',  # M/D/YYYY
        ]
        
        # Known schemas and their validation rules
        self.schema_rules = {
            'ohlcv-1d': {
                'required_fields': ['symbol', 'start_date', 'end_date'],
                'optional_fields': ['dataset'],
                'description': 'Daily OHLCV data'
            },
            'trades': {
                'required_fields': ['symbol', 'start_date', 'end_date'],
                'optional_fields': ['dataset'],
                'description': 'Trade-by-trade data'
            },
            'tbbo': {
                'required_fields': ['symbol', 'start_date', 'end_date'],
                'optional_fields': ['dataset'],
                'description': 'Top of book bid/offer data'
            },
            'statistics': {
                'required_fields': ['symbol', 'start_date', 'end_date'],
                'optional_fields': ['dataset'],
                'description': 'Market statistics data'
            }
        }
        
    def validate_symbol(self, symbol_input: str, interactive: bool = True) -> ValidationResult:
        """Validate symbol with interactive feedback and suggestions.
        
        Args:
            symbol_input: Symbol to validate
            interactive: Whether to provide interactive suggestions
            
        Returns:
            ValidationResult with suggestions
        """
        if not symbol_input or not symbol_input.strip():
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Symbol cannot be empty",
                suggestions=["ES.c.0", "NQ.c.0", "CL.c.0", "AAPL", "MSFT"]
            )
            
        symbol_input = symbol_input.strip().upper()
        
        # Check for exact match
        if self.symbol_cache.is_valid_symbol(symbol_input):
            symbol_info = self.symbol_cache.get_symbol_info(symbol_input)
            return ValidationResult(
                is_valid=True,
                level=ValidationLevel.SUCCESS,
                message=f"Valid symbol: {symbol_input}",
                metadata=symbol_info
            )
            
        # Find suggestions
        suggestions = self.symbol_cache.fuzzy_search(symbol_input, limit=5)
        
        if not suggestions:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Unknown symbol '{symbol_input}'. No similar symbols found.",
                suggestions=["ES.c.0", "NQ.c.0", "CL.c.0", "AAPL", "MSFT"]
            )
            
        # Build helpful error message with suggestions
        suggestion_list = [s[0] for s in suggestions]
        
        if interactive and suggestions:
            # Show interactive selection
            return self._interactive_symbol_selection(symbol_input, suggestion_list)
        else:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message=f"Symbol '{symbol_input}' not found. Did you mean:",
                suggestions=suggestion_list
            )
            
    def _interactive_symbol_selection(self, original_input: str, suggestions: List[str]) -> ValidationResult:
        """Show interactive symbol selection dialog.
        
        Args:
            original_input: Original user input
            suggestions: List of suggested symbols
            
        Returns:
            ValidationResult with user's choice
        """
        console.print(f"\n❓ Symbol '{original_input}' not found. Did you mean:")
        
        # Create selection table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Option", style="cyan", width=8)
        table.add_column("Symbol", style="green")
        table.add_column("Description", style="dim")
        
        for i, symbol in enumerate(suggestions, 1):
            symbol_info = self.symbol_cache.get_symbol_info(symbol)
            description = ""
            if symbol_info:
                asset_class = symbol_info.get('asset_class', '')
                sector = symbol_info.get('sector', '')
                if asset_class and sector:
                    description = f"{asset_class} - {sector}"
                elif asset_class:
                    description = asset_class
                    
            table.add_row(str(i), symbol, description)
            
        table.add_row("0", "None", "Keep original input")
        
        console.print(table)
        
        try:
            choice = IntPrompt.ask(
                "Select an option",
                choices=[str(i) for i in range(len(suggestions) + 1)],
                default="0"
            )
            
            if choice == 0:
                return ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.WARNING,
                    message=f"Keeping original input '{original_input}'",
                    corrected_value=original_input
                )
            else:
                selected_symbol = suggestions[choice - 1]
                symbol_info = self.symbol_cache.get_symbol_info(selected_symbol)
                return ValidationResult(
                    is_valid=True,
                    level=ValidationLevel.SUCCESS,
                    message=f"Selected symbol: {selected_symbol}",
                    corrected_value=selected_symbol,
                    metadata=symbol_info
                )
                
        except (KeyboardInterrupt, EOFError):
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Symbol selection cancelled by user"
            )
            
    def validate_date_range(self, start_date_str: str, end_date_str: str, 
                          symbol: str = None, interactive: bool = True) -> ValidationResult:
        """Validate date range with market calendar awareness.
        
        Args:
            start_date_str: Start date string
            end_date_str: End date string
            symbol: Optional symbol for asset-specific validation
            interactive: Whether to provide interactive suggestions
            
        Returns:
            ValidationResult with date range analysis
        """
        # Parse dates
        try:
            start_date = self._parse_date(start_date_str)
            end_date = self._parse_date(end_date_str)
        except ValueError as e:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Invalid date format: {e}",
                suggestions=["YYYY-MM-DD format (e.g., 2024-01-01)"]
            )
            
        # Basic date range validation
        if start_date >= end_date:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Start date must be before end date",
                suggestions=[
                    f"Try: start='{end_date - timedelta(days=30)}', end='{end_date}'"
                ]
            )
            
        # Check if dates are too far in the future
        today = date.today()
        if start_date > today:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message="Start date is in the future",
                suggestions=[f"Try: start='{today - timedelta(days=30)}'"]
            )
            
        # Market calendar analysis
        trading_days = self.market_calendar.get_trading_days(start_date, end_date, symbol)
        total_days = (end_date - start_date).days + 1
        non_trading_days = total_days - len(trading_days)
        
        # Build analysis
        analysis = {
            'start_date': start_date,
            'end_date': end_date,
            'total_days': total_days,
            'trading_days': len(trading_days),
            'non_trading_days': non_trading_days,
            'first_trading_day': trading_days[0] if trading_days else None,
            'last_trading_day': trading_days[-1] if trading_days else None,
            'coverage_ratio': len(trading_days) / total_days if total_days > 0 else 0
        }
        
        if not trading_days:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="No trading days in selected range",
                metadata=analysis,
                suggestions=[
                    f"Try extending range: start='{start_date - timedelta(days=7)}'"
                ]
            )
            
        # Success with analysis
        message_parts = [
            f"Valid date range: {len(trading_days)} trading days"
        ]
        
        if non_trading_days > 0:
            message_parts.append(f"({non_trading_days} non-trading days)")
            
        return ValidationResult(
            is_valid=True,
            level=ValidationLevel.SUCCESS,
            message=", ".join(message_parts),
            metadata=analysis
        )
        
    def _parse_date(self, date_str: str) -> date:
        """Parse date string in various formats.
        
        Args:
            date_str: Date string to parse
            
        Returns:
            Parsed date object
            
        Raises:
            ValueError: If date format is not recognized
        """
        date_str = date_str.strip()
        
        # Try common formats
        formats = [
            '%Y-%m-%d',    # 2024-01-01
            '%m/%d/%Y',    # 01/01/2024
            '%d/%m/%Y',    # 01/01/2024 (European)
            '%Y/%m/%d',    # 2024/01/01
            '%m-%d-%Y',    # 01-01-2024
            '%d-%m-%Y',    # 01-01-2024 (European)
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
                
        raise ValueError(f"Unrecognized date format: '{date_str}'. Use YYYY-MM-DD format.")
        
    def validate_schema(self, schema: str) -> ValidationResult:
        """Validate schema name and provide information.
        
        Args:
            schema: Schema name to validate
            
        Returns:
            ValidationResult with schema information
        """
        if not schema or not schema.strip():
            available_schemas = list(self.schema_rules.keys())
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Schema cannot be empty",
                suggestions=available_schemas
            )
            
        schema = schema.strip().lower()
        
        if schema in self.schema_rules:
            schema_info = self.schema_rules[schema]
            return ValidationResult(
                is_valid=True,
                level=ValidationLevel.SUCCESS,
                message=f"Valid schema: {schema} - {schema_info['description']}",
                metadata=schema_info
            )
        else:
            # Find close matches
            available_schemas = list(self.schema_rules.keys())
            suggestions = difflib.get_close_matches(schema, available_schemas, n=3, cutoff=0.6)
            
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Unknown schema: '{schema}'",
                suggestions=suggestions or available_schemas
            )
            
    def validate_symbol_list(self, symbols_str: str, interactive: bool = True) -> ValidationResult:
        """Validate a comma-separated list of symbols.
        
        Args:
            symbols_str: Comma-separated symbol string
            interactive: Whether to provide interactive suggestions
            
        Returns:
            ValidationResult with symbol list analysis
        """
        if not symbols_str or not symbols_str.strip():
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Symbol list cannot be empty",
                suggestions=["ES.c.0,NQ.c.0,CL.c.0"]
            )
            
        # Parse symbols
        symbols = [s.strip().upper() for s in symbols_str.split(',') if s.strip()]
        
        if not symbols:
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="No valid symbols found in list",
                suggestions=["ES.c.0,NQ.c.0,CL.c.0"]
            )
            
        # Validate each symbol
        valid_symbols = []
        invalid_symbols = []
        suggestions_map = {}
        
        for symbol in symbols:
            result = self.validate_symbol(symbol, interactive=False)
            if result.is_valid:
                valid_symbols.append(symbol)
            else:
                invalid_symbols.append(symbol)
                if result.suggestions:
                    suggestions_map[symbol] = result.suggestions
                    
        # Build result
        total_symbols = len(symbols)
        valid_count = len(valid_symbols)
        
        if valid_count == total_symbols:
            return ValidationResult(
                is_valid=True,
                level=ValidationLevel.SUCCESS,
                message=f"All {total_symbols} symbols are valid",
                metadata={
                    'valid_symbols': valid_symbols,
                    'total_count': total_symbols,
                    'valid_count': valid_count
                }
            )
        elif valid_count > 0:
            # Partial success
            suggestion_text = []
            for invalid_symbol in invalid_symbols:
                if invalid_symbol in suggestions_map:
                    suggestion_text.append(f"{invalid_symbol} → {suggestions_map[invalid_symbol][0]}")
                    
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.WARNING,
                message=f"{valid_count}/{total_symbols} symbols are valid. Invalid: {', '.join(invalid_symbols)}",
                suggestions=suggestion_text,
                metadata={
                    'valid_symbols': valid_symbols,
                    'invalid_symbols': invalid_symbols,
                    'suggestions_map': suggestions_map,
                    'total_count': total_symbols,
                    'valid_count': valid_count
                }
            )
        else:
            # All invalid
            return ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"No valid symbols found in: {', '.join(invalid_symbols)}",
                suggestions=["ES.c.0,NQ.c.0,CL.c.0"],
                metadata={
                    'invalid_symbols': invalid_symbols,
                    'suggestions_map': suggestions_map
                }
            )
            
    def show_validation_result(self, result: ValidationResult, title: str = "Validation Result"):
        """Display validation result with Rich formatting.
        
        Args:
            result: ValidationResult to display
            title: Title for the display panel
        """
        # Choose style based on level
        level_styles = {
            ValidationLevel.SUCCESS: ("✅", "green"),
            ValidationLevel.WARNING: ("⚠️", "yellow"),
            ValidationLevel.ERROR: ("❌", "red"),
            ValidationLevel.INFO: ("ℹ️", "blue")
        }
        
        icon, style = level_styles.get(result.level, ("•", "white"))
        
        # Build content
        content = f"{icon} {result.message}"
        
        if result.suggestions:
            content += "\n\n💡 Suggestions:"
            for suggestion in result.suggestions:
                content += f"\n  • {suggestion}"
                
        if result.corrected_value:
            content += f"\n\n✨ Corrected: {result.corrected_value}"
            
        # Show panel
        panel = Panel(content, title=title, border_style=style)
        console.print(panel)
        
    @lru_cache(maxsize=128)
    def get_completion_suggestions(self, input_text: str, context: str = "symbol") -> List[str]:
        """Get autocomplete suggestions for input.
        
        Args:
            input_text: Current input text
            context: Context for suggestions (symbol, schema, etc.)
            
        Returns:
            List of completion suggestions
        """
        if context == "symbol":
            suggestions = self.symbol_cache.fuzzy_search(input_text, limit=10)
            return [s[0] for s in suggestions]
        elif context == "schema":
            schemas = list(self.schema_rules.keys())
            if input_text:
                return [s for s in schemas if s.startswith(input_text.lower())]
            return schemas
        else:
            return []


def create_smart_validator() -> SmartValidator:
    """Create a SmartValidator instance with default configuration.
    
    Returns:
        Configured SmartValidator instance
    """
    return SmartValidator()


def validate_cli_input(input_value: Any, input_type: str, **kwargs) -> ValidationResult:
    """Convenience function for validating CLI inputs.
    
    Args:
        input_value: Value to validate
        input_type: Type of validation (symbol, date_range, schema, etc.)
        **kwargs: Additional validation parameters
        
    Returns:
        ValidationResult
    """
    validator = create_smart_validator()
    
    if input_type == "symbol":
        return validator.validate_symbol(str(input_value), **kwargs)
    elif input_type == "symbol_list":
        return validator.validate_symbol_list(str(input_value), **kwargs)
    elif input_type == "schema":
        return validator.validate_schema(str(input_value))
    elif input_type == "date_range":
        start_date = kwargs.pop('start_date', '')
        end_date = kwargs.pop('end_date', '')
        return validator.validate_date_range(start_date, end_date, **kwargs)
    else:
        return ValidationResult(
            is_valid=False,
            level=ValidationLevel.ERROR,
            message=f"Unknown validation type: {input_type}"
        )