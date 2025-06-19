"""
Common utility functions for CLI commands.
"""

import re
from datetime import datetime, date
from typing import List, Dict

import typer
from rich.console import Console

from utils.custom_logger import get_logger

console = Console()
logger = get_logger(__name__)


def validate_date_format(date_str: str) -> bool:
    """Validate date string is in YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def parse_date_string(date_str: str) -> date:
    """Parse date string to date object."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def parse_symbols(symbols_str: str) -> list[str]:
    """Parse comma-separated symbols string into list."""
    return [symbol.strip() for symbol in symbols_str.split(",") if symbol.strip()]


def parse_query_symbols(symbols_input: List[str]) -> List[str]:
    """Parse symbols from CLI input (handles both comma-separated and multiple flags)."""
    parsed_symbols = []
    for symbol_group in symbols_input:
        if "," in symbol_group:
            # Handle comma-separated: "ES.c.0,NQ.c.0"
            parsed_symbols.extend([s.strip() for s in symbol_group.split(",") if s.strip()])
        else:
            # Handle single symbol
            symbol = symbol_group.strip()
            if symbol:  # Only add non-empty symbols
                parsed_symbols.append(symbol)
    return parsed_symbols


def validate_symbol_stype_combination(symbols: List[str], stype_in: str) -> List[str]:
    """Validate that symbols match the expected format for the given stype_in.
    
    Args:
        symbols: List of symbols to validate
        stype_in: Symbol type (continuous, parent, native)
        
    Returns:
        List of validation error messages (empty if all valid)
    """
    errors = []
    
    # Define patterns for each stype_in
    patterns = {
        "continuous": {
            "pattern": r"^[A-Z0-9]+\.(c|n)\.\d+$",  # e.g., ES.c.0, NG.c.1, TEST0.c.0
            "example": "ES.c.0 or NG.c.0",
            "description": "continuous contracts"
        },
        "parent": {
            "pattern": r"^[A-Z0-9]+\.(FUT|OPT|IVX|MLP)$",  # e.g., ES.FUT, CL.FUT
            "example": "ES.FUT or NG.FUT",
            "description": "parent symbols"
        },
        "native": {
            "pattern": r"^[A-Z0-9]+$",  # e.g., SPY, AAPL, SPY500
            "example": "SPY or AAPL",
            "description": "native equity symbols"
        }
    }
    
    if stype_in not in patterns:
        errors.append(f"Invalid stype_in '{stype_in}'. Must be one of: continuous, parent, native")
        return errors
        
    pattern_info = patterns[stype_in]
    pattern = re.compile(pattern_info["pattern"])
    
    invalid_symbols = []
    for symbol in symbols:
        # Special case: ALL_SYMBOLS is allowed with any stype_in
        if symbol == "ALL_SYMBOLS":
            continue
        if not pattern.match(symbol):
            invalid_symbols.append(symbol)
            
    if invalid_symbols:
        errors.append(
            f"Invalid symbols for stype_in='{stype_in}': {', '.join(invalid_symbols)}. "
            f"Expected format for {pattern_info['description']}: {pattern_info['example']}"
        )
        
        # Provide specific suggestions for common mistakes
        for symbol in invalid_symbols:
            if stype_in == "continuous" and symbol.endswith(".FUT"):
                errors.append(
                    f"💡 '{symbol}' looks like a parent symbol. "
                    f"For continuous contracts, use '{symbol.replace('.FUT', '.c.0')}' "
                    f"or change stype_in to 'parent'"
                )
            elif stype_in == "parent" and ".c." in symbol:
                root = symbol.split(".")[0]
                errors.append(
                    f"💡 '{symbol}' looks like a continuous contract. "
                    f"For parent symbols, use '{root}.FUT' "
                    f"or change stype_in to 'continuous'"
                )
                
    return errors


def validate_query_scope(symbols: List[str], start_date: date, end_date: date, schema: str) -> bool:
    """Validate query scope and warn about large result sets."""
    days = (end_date - start_date).days

    if schema == "trades" and days > 1:
        console.print("⚠️  [yellow]Warning: Trades data for multiple days can be very large[/yellow]")
        return typer.confirm("Continue with this query?")

    if schema == "tbbo" and days > 1:
        console.print("⚠️  [yellow]Warning: TBBO data for multiple days can be very large[/yellow]")
        return typer.confirm("Continue with this query?")

    if len(symbols) > 10:
        console.print(f"⚠️  [yellow]Warning: Querying {len(symbols)} symbols may take some time[/yellow]")
        return typer.confirm("Continue with this query?")

    return True