"""
Main entry point for the Historical Data Ingestor application.

This module provides the command-line interface for executing data ingestion
pipelines, querying stored data, and managing the system.
"""

from utils.custom_logger import setup_logging, get_logger, log_status, log_progress, log_user_message
from querying.exceptions import QueryingError, SymbolResolutionError, QueryExecutionError
from querying import QueryBuilder
from core.pipeline_orchestrator import PipelineOrchestrator, PipelineError
from cli.help_utils import (
    CLIExamples, CLITroubleshooter, CLITips,
    show_examples, show_tips, validate_date_range, validate_symbols,
    format_schema_help, suggest_date_range
)
from cli.enhanced_help_utils import (
    InteractiveHelpMenu, QuickstartWizard, WorkflowExamples,
    CheatSheet, SymbolHelper, GuidedMode
)
from cli.progress_utils import EnhancedProgress, MetricsDisplay, LiveStatusDashboard, OperationMonitor, format_duration
from cli.symbol_groups import SymbolGroupManager
from cli.smart_validation import SmartValidator, create_smart_validator, validate_cli_input
from cli.interactive_workflows import (
    WorkflowBuilder, create_interactive_workflow, list_saved_workflows, 
    load_workflow_by_name
)
from cli.config_manager import ConfigManager, get_config_manager, get_config
import csv
import json
import os
import sys
from datetime import datetime, date
from decimal import Decimal
from io import StringIO
from pathlib import Path
from typing import Optional, List, Dict

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from dotenv import load_dotenv

try:
    import pandas_market_calendars as pmc  # type: ignore
    PANDAS_MARKET_CALENDARS_AVAILABLE = True
except ImportError:
    pmc = None
    PANDAS_MARKET_CALENDARS_AVAILABLE = False

# Load environment variables from .env file (override existing env vars)
load_dotenv(override=True)

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))


# Initialize the Typer app
app = typer.Typer(
    name="hist-data-ingestor",
    help="""📊 Historical Data Ingestor - Financial Market Data Pipeline
    
A production-ready system for ingesting, processing, and querying historical financial data.
Supports multiple data schemas (OHLCV, trades, quotes) with intelligent symbol resolution.
    
Quick Start:
  python main.py status              # Check system health
  python main.py quickstart          # Interactive setup wizard
  python main.py help-menu           # Interactive help system
  python main.py examples            # Show usage examples
  python main.py cheatsheet          # Quick reference guide
    
For troubleshooting: python main.py troubleshoot
    """,
    no_args_is_help=True,
    pretty_exceptions_show_locals=False
)

# Initialize Rich console for better output
console = Console()

# Set up logging with configuration-based levels
try:
    config = get_config()
    setup_logging(
        log_level=config.logging.level,
        log_file=config.logging.file,
        console_level=config.logging.console_level
    )
except Exception:
    # Fallback if config loading fails
    setup_logging(log_level="DEBUG", console_level="WARNING")

logger = get_logger(__name__)

# Schema mapping for CLI query command
SCHEMA_MAPPING = {
    "ohlcv-1d": "query_daily_ohlcv",
    "ohlcv": "query_daily_ohlcv",  # Alias
    "trades": "query_trades",
    "tbbo": "query_tbbo",
    "statistics": "query_statistics",
    "definitions": "query_definitions"
}


def validate_date_format(date_str: str) -> bool:
    """Validate date string is in YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


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


def parse_date_string(date_str: str) -> date:
    """Parse date string to date object."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


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
        
    import re
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


def format_table_output(results: List[Dict], schema: str) -> Table:
    """Format query results as Rich table for console display."""
    table = Table(show_header=True, header_style="bold magenta")

    if not results:
        table.add_column("Message")
        table.add_row("No data found for the specified criteria.")
        return table

    # Add columns based on schema
    if schema.startswith("ohlcv"):
        table.add_column("Symbol")
        table.add_column("Date")
        table.add_column("Open")
        table.add_column("High")
        table.add_column("Low")
        table.add_column("Close")
        table.add_column("Volume")

        for row in results:
            table.add_row(
                str(row.get("symbol", "")),
                str(row.get("ts_event", "")).split("T")[0] if row.get("ts_event") else "",
                str(row.get("open_price", "")),
                str(row.get("high_price", "")),
                str(row.get("low_price", "")),
                str(row.get("close_price", "")),
                str(row.get("volume", ""))
            )
    elif schema == "trades":
        table.add_column("Symbol")
        table.add_column("Timestamp")
        table.add_column("Price")
        table.add_column("Size")
        table.add_column("Side")

        for row in results:
            table.add_row(
                str(row.get("symbol", "")),
                str(row.get("ts_event", "")),
                str(row.get("price", "")),
                str(row.get("size", "")),
                str(row.get("side", ""))
            )
    elif schema == "tbbo":
        table.add_column("Symbol")
        table.add_column("Timestamp")
        table.add_column("Bid Price")
        table.add_column("Bid Size")
        table.add_column("Ask Price")
        table.add_column("Ask Size")

        for row in results:
            table.add_row(
                str(row.get("symbol", "")),
                str(row.get("ts_event", "")),
                str(row.get("bid_px_00", "")),
                str(row.get("bid_sz_00", "")),
                str(row.get("ask_px_00", "")),
                str(row.get("ask_sz_00", ""))
            )
    elif schema == "statistics":
        table.add_column("Symbol")
        table.add_column("Timestamp")
        table.add_column("Stat Type")
        table.add_column("Value")
        table.add_column("Update Action")

        for row in results:
            table.add_row(
                str(row.get("symbol", "")),
                str(row.get("ts_event", "")),
                str(row.get("stat_type", "")),
                str(row.get("stat_value", "")),
                str(row.get("update_action", ""))
            )
    elif schema == "definitions":
        table.add_column("Symbol")
        table.add_column("Raw Symbol")
        table.add_column("Asset")
        table.add_column("Exchange")
        table.add_column("Currency")
        table.add_column("Tick Size")

        for row in results:
            table.add_row(
                str(row.get("symbol", "")),
                str(row.get("raw_symbol", "")),
                str(row.get("asset", "")),
                str(row.get("exchange", "")),
                str(row.get("currency", "")),
                str(row.get("tick_size", ""))
            )
    else:
        # Generic table for unknown schemas
        if results:
            for key in results[0].keys():
                table.add_column(key.replace("_", " ").title())

            for row in results:
                table.add_row(*[str(value) for value in row.values()])

    return table


def format_csv_output(results: List[Dict]) -> str:
    """Format query results as CSV string."""
    if not results:
        return ""

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=results[0].keys())
    writer.writeheader()

    for row in results:
        # Handle Decimal and datetime serialization
        serialized_row = {}
        for key, value in row.items():
            if isinstance(value, Decimal):
                serialized_row[key] = str(value)
            elif isinstance(value, datetime):
                serialized_row[key] = value.isoformat()
            else:
                serialized_row[key] = value
        writer.writerow(serialized_row)

    return output.getvalue()


def format_json_output(results: List[Dict]) -> str:
    """Format query results as JSON string."""
    def json_serializer(obj):
        if isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    return json.dumps(results, indent=2, default=json_serializer)


def write_output_file(content: str, file_path: str, _format_type: str):
    """Write formatted content to file with proper error handling."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        console.print(f"✅ [green]Output written to {file_path}[/green]")
    except IOError as e:
        console.print(f"❌ [red]Failed to write file {file_path}: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def query(
    symbols: List[str] = typer.Option(
        ...,
        "--symbols", "-s",
        help="Security symbols (e.g., ES.c.0, NQ.c.0). Can be comma-separated or multiple -s flags"
    ),
    start_date: str = typer.Option(
        ...,
        "--start-date", "-sd",
        help="Start date (YYYY-MM-DD)"
    ),
    end_date: str = typer.Option(
        ...,
        "--end-date", "-ed",
        help="End date (YYYY-MM-DD)"
    ),
    schema: str = typer.Option(
        "ohlcv-1d",
        "--schema",
        help="Schema type (ohlcv-1d, trades, tbbo, statistics, definitions)"
    ),
    output_format: str = typer.Option(
        "table",
        "--output-format", "-f",
        help="Output format (table, csv, json)"
    ),
    output_file: Optional[str] = typer.Option(
        None,
        "--output-file", "-o",
        help="Output file path"
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        help="Limit number of results. Useful for large datasets like trades/tbbo."
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview query without execution. Shows what would be queried."
    ),
    validate_only: bool = typer.Option(
        False,
        "--validate-only",
        help="Validate parameters without executing query. Useful for testing."
    ),
    guided: bool = typer.Option(
        False,
        "--guided",
        help="Use interactive guided mode to select parameters"
    ),
):
    """
    Query historical financial data from TimescaleDB with intelligent symbol resolution.
    
    This command supports multiple data schemas, output formats, and flexible date ranges.
    Symbol resolution automatically maps user-friendly symbols to instrument IDs.

    Examples:
        # Basic daily OHLCV query
        python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31
        
        # Multiple symbols with CSV export
        python main.py query --symbols ES.c.0,NQ.c.0,CL.c.0 \\
            --start-date 2024-01-01 --end-date 2024-01-31 \\
            --output-format csv --output-file results.csv
        
        # High-frequency trades data (single day recommended)
        python main.py query -s ES.c.0 --schema trades \\
            --start-date 2024-01-15 --end-date 2024-01-15 \\
            --limit 1000 --output-format json
        
        # Preview query without execution
        python main.py query -s ES.c.0 --start-date 2024-01-01 \\
            --end-date 2024-01-31 --dry-run
    
    Tips:
        - Use 'python main.py examples query' for more examples
        - Use 'python main.py schemas' to see available data types
        - For large datasets (trades/tbbo), use --limit parameter
        - Date format must be YYYY-MM-DD
    """
    # Handle guided mode
    if guided:
        guided_params = GuidedMode.guided_query()
        symbols = guided_params.get('symbols', symbols)
        start_date = guided_params.get('start_date', start_date)
        end_date = guided_params.get('end_date', end_date)
        schema = guided_params.get('schema', schema)
        output_format = guided_params.get('output_format', output_format)
        output_file = guided_params.get('output_file', output_file)
        limit = guided_params.get('limit', limit)
        dry_run = guided_params.get('dry_run', dry_run)
    
    console.print("🔍 [bold blue]Querying historical financial data[/bold blue]")

    try:
        # Parse and validate symbols
        parsed_symbols = parse_query_symbols(symbols)
        if not parsed_symbols:
            console.print("❌ [red]Error: No valid symbols provided[/red]")
            console.print("💡 [yellow]Example: --symbols ES.c.0,NQ.c.0 or -s ES.c.0 -s NQ.c.0[/yellow]")
            raise typer.Exit(1)
            
        # Enhanced symbol validation
        symbol_valid, symbol_msg = validate_symbols(parsed_symbols)
        if not symbol_valid and validate_only:
            console.print(f"⚠️  [yellow]Symbol validation warning:[/yellow]")
            console.print(symbol_msg)

        # Validate date format with helpful messages
        if not validate_date_format(start_date):
            console.print("❌ [red]Error: Invalid start-date format[/red]")
            console.print(f"💡 [yellow]Expected format: YYYY-MM-DD (e.g., {datetime.now().strftime('%Y-%m-%d')})[/yellow]")
            console.print(f"💡 [yellow]You provided: {start_date}[/yellow]")
            raise typer.Exit(1)

        if not validate_date_format(end_date):
            console.print("❌ [red]Error: Invalid end-date format[/red]")
            console.print(f"💡 [yellow]Expected format: YYYY-MM-DD (e.g., {datetime.now().strftime('%Y-%m-%d')})[/yellow]")
            console.print(f"💡 [yellow]You provided: {end_date}[/yellow]")
            raise typer.Exit(1)

        # Parse dates
        start_date_obj = parse_date_string(start_date)
        end_date_obj = parse_date_string(end_date)

        # Enhanced date range validation
        date_valid, date_msg = validate_date_range(start_date, end_date)
        if not date_valid:
            console.print(f"❌ [red]Error: {date_msg}[/red]")
            raise typer.Exit(1)

        # Market calendar pre-flight check for query optimization
        if not dry_run:
            try:
                from cli.smart_validation import SmartValidator
                
                # Determine appropriate exchange using intelligent mapping
                exchange = "NYSE"  # Default fallback
                if parsed_symbols:
                    from cli.exchange_mapping import map_symbols_to_exchange
                    exchange, confidence = map_symbols_to_exchange(parsed_symbols, "NYSE")
                    console.print(f"🎯 [cyan]Auto-detected exchange: {exchange} (confidence: {confidence:.2f})[/cyan]")
                
                # Create validator and analyze date range
                validator = SmartValidator(exchange_name=exchange)
                
                validation_result = validator.validate_date_range(start_date_obj, end_date_obj)
                
                # Extract trading day coverage
                coverage_pct = validation_result.metadata.get('coverage_ratio', 0) * 100
                trading_days = validation_result.metadata.get('trading_days', 0)
                total_days = validation_result.metadata.get('total_days', 0)
                
                # Show pre-flight analysis for query
                console.print(f"\n📅 [bold cyan]Market Calendar Pre-flight Analysis ({exchange}):[/bold cyan]")
                console.print(f"Date Range: {start_date} to {end_date}")
                console.print(f"Trading Days: {trading_days}/{total_days} ({coverage_pct:.1f}% coverage)")
                
                # Warning if coverage is low
                if coverage_pct < 30:
                    console.print("[red]⚠️  WARNING: Very low trading day coverage![/red]")
                    console.print(f"[red]   Query may return sparse data: ~{100-coverage_pct:.0f}% of requested period has no trading[/red]")
                    console.print(f"[yellow]   Consider using: python main.py market-calendar {start_date} {end_date} --exchange {exchange} --holidays[/yellow]")
                    
                    if not validate_only:
                        continue_anyway = typer.confirm("Continue with this date range anyway?")
                        if not continue_anyway:
                            console.print("💡 [cyan]Tips for better query ranges:[/cyan]")
                            console.print("   • Use python main.py market-calendar to analyze dates first")
                            console.print("   • Consider focusing on trading days only")
                            console.print("   • Exclude major holiday periods")
                            raise typer.Exit(0)
                        
                elif coverage_pct < 60:
                    console.print("[yellow]⚠️  Moderate trading day coverage - query may have gaps[/yellow]")
                    console.print(f"[blue]💡 Consider focusing on trading-heavy periods for better data density[/blue]")
                else:
                    console.print("[green]✅ Good trading day coverage for comprehensive data[/green]")

                # Check for early closes in the date range
                try:
                    early_closes = validator.market_calendar.get_early_closes(start_date_obj, end_date_obj)
                    if early_closes:
                        console.print(f"\n🕐 [yellow]Early Market Closes Detected ({len(early_closes)}):[/yellow]")
                        for close_date, close_info in sorted(early_closes.items()):
                            date_str = close_date.strftime("%Y-%m-%d (%a)")
                            console.print(f"   • {date_str}: {close_info}")
                        console.print("[blue]💡 Early closes may result in partial trading data for these dates[/blue]")
                except Exception:
                    pass  # Don't fail if early close detection fails
                    
            except Exception as e:
                # Don't fail the entire command if pre-flight check fails
                console.print(f"[yellow]⚠️  Could not perform market calendar analysis: {e}[/yellow]")
                console.print("[yellow]   Continuing with query...[/yellow]")

        # Validate schema
        if schema not in SCHEMA_MAPPING:
            valid_schemas = ', '.join(SCHEMA_MAPPING.keys())
            console.print(
                f"❌ [red]Error: Invalid schema '{schema}'. Valid options: {valid_schemas}[/red]"
            )
            raise typer.Exit(1)

        # Validate output format
        if output_format not in ["table", "csv", "json"]:
            console.print("❌ [red]Error: Invalid output format[/red]")
            console.print("💡 [yellow]Valid options: table (human-readable), csv (Excel), json (API)[/yellow]")
            raise typer.Exit(1)
            
        # If validate_only, show validation results and exit
        if validate_only:
            console.print("\n✅ [bold green]Parameter validation successful![/bold green]")
            console.print("📋 [cyan]Validated configuration:[/cyan]")
            validation_table = Table(show_header=True, header_style="bold magenta")
            validation_table.add_column("Parameter")
            validation_table.add_column("Value")
            validation_table.add_column("Status")
            
            validation_table.add_row("Symbols", ", ".join(parsed_symbols), "✅ Valid")
            validation_table.add_row("Date Range", f"{start_date} to {end_date}", "✅ Valid")
            validation_table.add_row("Schema", schema, "✅ Valid")
            validation_table.add_row("Output Format", output_format, "✅ Valid")
            
            console.print(validation_table)
            console.print("\n💡 [yellow]Remove --validate-only to execute the query[/yellow]")
            raise typer.Exit(0)

        # Validate query scope and get user confirmation if needed
        if not dry_run and not validate_query_scope(parsed_symbols, start_date_obj, end_date_obj, schema):
            console.print("⏹️  [yellow]Query cancelled by user[/yellow]")
            raise typer.Exit(0)

        # Display query configuration
        console.print("📋 [cyan]Query configuration:[/cyan]")
        config_table = Table(show_header=True, header_style="bold magenta")
        config_table.add_column("Parameter")
        config_table.add_column("Value")

        config_table.add_row("Symbols", ", ".join(parsed_symbols))
        config_table.add_row("Date Range", f"{start_date} to {end_date}")
        config_table.add_row("Schema", schema)
        config_table.add_row("Output Format", output_format)
        if output_file:
            config_table.add_row("Output File", output_file)
        if limit:
            config_table.add_row("Limit", str(limit))
        if dry_run:
            config_table.add_row("Mode", "🎭 DRY RUN")

        console.print(config_table)
        
        # If dry run, show what would happen and exit
        if dry_run:
            console.print("\n🎭 [bold yellow]DRY RUN MODE - No query will be executed[/bold yellow]")
            console.print("\n📋 [cyan]What would happen:[/cyan]")
            console.print(f"  1. Connect to TimescaleDB database")
            console.print(f"  2. Resolve symbols {parsed_symbols} to instrument IDs")
            console.print(f"  3. Query {schema} data for date range {start_date} to {end_date}")
            console.print(f"  4. Format results as {output_format}")
            if output_file:
                console.print(f"  5. Save results to {output_file}")
            else:
                console.print(f"  5. Display results in terminal")
            console.print("\n💡 [yellow]Remove --dry-run to execute the query[/yellow]")
            raise typer.Exit(0)

        # Execute query with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Querying {schema} data for {len(parsed_symbols)} symbols...", total=None)

            start_time = datetime.now()

            # Initialize QueryBuilder
            qb = QueryBuilder()

            # Get the appropriate query method
            query_method_name = SCHEMA_MAPPING[schema]
            query_method = getattr(qb, query_method_name)

            # Build query parameters
            query_params = {
                "symbols": parsed_symbols,
                "start_date": start_date_obj,
                "end_date": end_date_obj
            }

            if limit:
                query_params["limit"] = limit

            # Execute query
            results = query_method(**query_params)

            progress.update(task, completed=True)

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

        # Handle results
        if not results:
            console.print("ℹ️  [yellow]No data found for the specified criteria.[/yellow]")
            if output_file:
                # Write empty file
                write_output_file("", output_file, output_format)
            return

        console.print(f"✅ [green]Found {len(results)} records in {execution_time:.2f} seconds[/green]")

        # Format and display/save results
        if output_format == "table":
            table = format_table_output(results, schema)
            if output_file:
                # For table format to file, use CSV instead
                csv_content = format_csv_output(results)
                write_output_file(csv_content, output_file, "csv")
                console.print("ℹ️  [yellow]Note: Table format saved as CSV to file[/yellow]")
            else:
                console.print("\n📊 [bold cyan]Query Results:[/bold cyan]")
                console.print(table)

        elif output_format == "csv":
            csv_content = format_csv_output(results)
            if output_file:
                write_output_file(csv_content, output_file, "csv")
            else:
                console.print("\n📊 [bold cyan]Query Results (CSV):[/bold cyan]")
                console.print(csv_content)

        elif output_format == "json":
            json_content = format_json_output(results)
            if output_file:
                write_output_file(json_content, output_file, "json")
            else:
                console.print("\n📊 [bold cyan]Query Results (JSON):[/bold cyan]")
                console.print(json_content)

        # Display summary
        console.print("\n📈 [bold green]Query completed successfully![/bold green]")
        console.print(f"Records: {len(results)} | Time: {execution_time:.2f}s | Schema: {schema}")

    except SymbolResolutionError as e:
        console.print(f"❌ [red]Symbol error: {e}[/red]")
        
        # Show troubleshooting help
        CLITroubleshooter.show_help(str(e))

        # Show available symbols
        try:
            qb = QueryBuilder()
            available = qb.get_available_symbols(limit=10)
            if available:
                console.print("\n📊 [yellow]Available symbols (sample):[/yellow]")
                for symbol in available[:5]:
                    console.print(f"   • {symbol}")
                console.print("\n💡 [yellow]Tips:[/yellow]")
                console.print("   • Use 'python main.py examples query' for symbol format examples")
                console.print("   • Ensure symbol data has been ingested first")
                console.print("   • Check date range - symbol might not have data for those dates")
        except Exception:
            pass  # Don't fail if we can't get available symbols

        logger.error("Symbol resolution failed", error=str(e), symbols=parsed_symbols)
        raise typer.Exit(1)

    except QueryExecutionError as e:
        console.print(f"❌ [red]Database error: {e}[/red]")
        
        # Show troubleshooting help
        CLITroubleshooter.show_help("Database connection failed")
        
        console.print("\n💡 [yellow]Quick checks:[/yellow]")
        console.print("   • Run 'python main.py status' to check database connectivity")
        console.print("   • Ensure TimescaleDB container is running: docker-compose ps")
        console.print("   • Check environment variables are loaded")
        
        logger.error("Query execution failed", error=str(e))
        raise typer.Exit(1)

    except QueryingError as e:
        console.print(f"❌ [red]Query error: {e}[/red]")
        
        # Try to provide specific help based on error
        CLITroubleshooter.show_help(str(e))
        
        logger.error("General querying error", error=str(e))
        raise typer.Exit(1)

    except Exception as e:
        console.print(f"❌ [red]Unexpected error: {e}[/red]")
        console.print("\n🔧 [yellow]Troubleshooting:[/yellow]")
        console.print("   • Check logs for details: tail -f logs/app.log")
        console.print("   • Run 'python main.py troubleshoot' for common issues")
        console.print("   • Verify your environment setup")
        logger.error("Unexpected error in query command", error=str(e), error_type=type(e).__name__)
        raise typer.Exit(1)


@app.command()
def ingest(
    api: str = typer.Option(..., help="API provider. Currently supports: databento"),
    job: Optional[str] = typer.Option(None, help="Predefined job name from config file. Use 'list-jobs' to see available jobs."),
    dataset: Optional[str] = typer.Option(None, help="Dataset identifier (e.g., GLBX.MDP3 for CME Globex)"),
    schema: Optional[str] = typer.Option(None, help="Data schema: ohlcv-1d (daily bars), trades, tbbo (quotes), statistics, definitions"),
    symbols: Optional[str] = typer.Option(None, help="Comma-separated symbols (e.g., ES.FUT,CL.FUT). See 'examples ingest' for formats."),
    start_date: Optional[str] = typer.Option(None, help="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = typer.Option(None, help="End date in YYYY-MM-DD format (inclusive)"),
    stype_in: Optional[str] = typer.Option(None, help="Symbol type: continuous (c.0), native, parent (.FUT)"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview ingestion without execution"),
    guided: bool = typer.Option(False, "--guided", help="Use interactive guided mode to select parameters"),
):
    """
    Execute a data ingestion pipeline to fetch and store financial market data.
    
    Supports two modes:
    1. Predefined jobs: Use --job parameter with a configured job name
    2. Custom parameters: Specify dataset, schema, symbols, and date range

    Examples:
        # Use a predefined job from config
        python main.py ingest --api databento --job ohlcv_1d
        
        # Custom daily OHLCV ingestion
        python main.py ingest --api databento --dataset GLBX.MDP3 \\
            --schema ohlcv-1d --symbols ES.FUT,CL.FUT \\
            --start-date 2024-01-01 --end-date 2024-01-31
        
        # Ingest high-frequency trades data (single day recommended)
        python main.py ingest --api databento --dataset GLBX.MDP3 \\
            --schema trades --symbols ES.c.0 \\
            --start-date 2024-01-15 --end-date 2024-01-15
        
        # Preview ingestion without execution
        python main.py ingest --api databento --job ohlcv_1d --dry-run
    
    Tips:
        - Use 'python main.py list-jobs' to see available predefined jobs
        - Use 'python main.py examples ingest' for more examples
        - Large date ranges are automatically batched for efficiency
        - Failed records are quarantined in dlq/ directory
    """
    # Handle guided mode
    if guided:
        guided_params = GuidedMode.guided_ingest()
        api = guided_params.get('api', api)
        job = guided_params.get('job')
        dataset = guided_params.get('dataset')
        schema = guided_params.get('schema')
        symbols = guided_params.get('symbols')
        start_date = guided_params.get('start_date')
        end_date = guided_params.get('end_date')
        stype_in = guided_params.get('stype_in')
    
    console.print(f"🚀 [bold blue]Starting {api.upper()} data ingestion pipeline[/bold blue]")

    try:
        # Validate inputs
        if not job and not all([dataset, schema, symbols, start_date, end_date]):
            console.print("❌ [red]Error: Missing required parameters[/red]")
            console.print("\n💡 [yellow]You have two options:[/yellow]")
            console.print("  1. Use a predefined job: --job <job_name>")
            console.print("  2. Provide custom parameters: --dataset, --schema, --symbols, --start-date, --end-date")
            console.print("\n📖 [cyan]Examples:[/cyan]")
            console.print("  python main.py ingest --api databento --job ohlcv_1d")
            console.print("  python main.py ingest --api databento --dataset GLBX.MDP3 --schema ohlcv-1d \\")
            console.print("      --symbols ES.FUT --start-date 2024-01-01 --end-date 2024-01-31")
            console.print("\nUse 'python main.py examples ingest' for more examples")
            raise typer.Exit(1)

        if start_date and not validate_date_format(start_date):
            console.print("❌ [red]Error: Invalid start-date format[/red]")
            console.print(f"💡 [yellow]Expected: YYYY-MM-DD (e.g., {datetime.now().strftime('%Y-%m-%d')})[/yellow]")
            console.print(f"💡 [yellow]You provided: {start_date}[/yellow]")
            raise typer.Exit(1)

        if end_date and not validate_date_format(end_date):
            console.print("❌ [red]Error: Invalid end-date format[/red]")
            console.print(f"💡 [yellow]Expected: YYYY-MM-DD (e.g., {datetime.now().strftime('%Y-%m-%d')})[/yellow]")
            console.print(f"💡 [yellow]You provided: {end_date}[/yellow]")
            raise typer.Exit(1)
            
        # Validate date range if both dates provided
        if start_date and end_date:
            date_valid, date_msg = validate_date_range(start_date, end_date)
            if not date_valid:
                console.print(f"❌ [red]Error: {date_msg}[/red]")
                raise typer.Exit(1)

        # Market calendar pre-flight check for cost optimization
        if start_date and end_date and not dry_run:
            try:
                from cli.smart_validation import SmartValidator
                from datetime import datetime
                
                # Determine appropriate exchange using intelligent mapping
                exchange = "NYSE"  # Default fallback
                if symbols:
                    symbol_list = parse_symbols(symbols) if isinstance(symbols, str) else symbols
                    from cli.exchange_mapping import map_symbols_to_exchange
                    exchange, confidence = map_symbols_to_exchange(symbol_list, "NYSE")
                    console.print(f"🎯 [cyan]Auto-detected exchange: {exchange} (confidence: {confidence:.2f})[/cyan]")
                
                # Create validator and analyze date range
                validator = SmartValidator(exchange_name=exchange)
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
                
                validation_result = validator.validate_date_range(start_dt, end_dt)
                
                # Extract trading day coverage
                coverage_pct = validation_result.metadata.get('coverage_ratio', 0) * 100
                trading_days = validation_result.metadata.get('trading_days', 0)
                total_days = validation_result.metadata.get('total_days', 0)
                
                # Show pre-flight analysis
                console.print(f"\n📅 [bold cyan]Market Calendar Pre-flight Analysis ({exchange}):[/bold cyan]")
                console.print(f"Date Range: {start_date} to {end_date}")
                console.print(f"Trading Days: {trading_days}/{total_days} ({coverage_pct:.1f}% coverage)")
                
                # Warning if coverage is low
                if coverage_pct < 30:
                    console.print("[red]⚠️  WARNING: Very low trading day coverage![/red]")
                    console.print(f"[red]   Potential API cost waste: ~{100-coverage_pct:.0f}% of requests may return no data[/red]")
                    console.print(f"[yellow]   Consider using: python main.py market-calendar {start_date} {end_date} --exchange {exchange} --holidays[/yellow]")
                    
                    if not force:
                        continue_anyway = typer.confirm("Continue with this date range anyway?")
                        if not continue_anyway:
                            console.print("💡 [cyan]Tips for better date ranges:[/cyan]")
                            console.print("   • Use python main.py market-calendar to analyze dates first")
                            console.print("   • Consider excluding holiday periods")
                            console.print("   • Focus on periods with high trading activity")
                            raise typer.Exit(0)
                        
                elif coverage_pct < 60:
                    console.print("[yellow]⚠️  Moderate trading day coverage - consider optimization[/yellow]")
                    console.print(f"[blue]💰 Potential API savings: ~{100-coverage_pct:.0f}% by excluding non-trading days[/blue]")
                else:
                    console.print("[green]✅ Good trading day coverage for API efficiency[/green]")

                # Check for early closes in the date range
                try:
                    early_closes = validator.market_calendar.get_early_closes(start_dt, end_dt)
                    if early_closes:
                        console.print(f"\n🕐 [yellow]Early Market Closes Detected ({len(early_closes)}):[/yellow]")
                        for close_date, close_info in sorted(early_closes.items()):
                            date_str = close_date.strftime("%Y-%m-%d (%a)")
                            console.print(f"   • {date_str}: {close_info}")
                        console.print("[blue]💡 Early closes may affect data completeness for intraday schemas[/blue]")
                except Exception:
                    pass  # Don't fail if early close detection fails
                    
            except Exception as e:
                # Don't fail the entire command if pre-flight check fails
                console.print(f"[yellow]⚠️  Could not perform market calendar analysis: {e}[/yellow]")
                console.print("[yellow]   Continuing with ingestion...[/yellow]")

        # Build overrides dictionary for custom parameters
        overrides = {}
        if dataset:
            overrides["dataset"] = dataset
        if schema:
            overrides["schema"] = schema
        if symbols:
            overrides["symbols"] = parse_symbols(symbols)
        if start_date:
            overrides["start_date"] = start_date
        if end_date:
            overrides["end_date"] = end_date
        if stype_in:
            overrides["stype_in"] = stype_in

        # Display job configuration
        if job:
            console.print(f"📋 [cyan]Using predefined job: {job}[/cyan]")
            if overrides:
                console.print("🔧 [yellow]With parameter overrides:[/yellow]")
                override_table = Table(show_header=True, header_style="bold magenta")
                override_table.add_column("Parameter")
                override_table.add_column("Override Value")
                for key, value in overrides.items():
                    override_table.add_row(key.replace("_", " ").title(), str(value))
                console.print(override_table)
        else:
            console.print("📋 [cyan]Custom job configuration:[/cyan]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Parameter")
            table.add_column("Value")

            table.add_row("API Provider", api.upper())
            table.add_row("Dataset", dataset or "Not specified")
            table.add_row("Schema", schema or "Not specified")
            table.add_row("Symbols", str(overrides.get("symbols", [])) if overrides.get("symbols") else "Not specified")
            table.add_row("Date Range", f"{start_date or 'Not specified'} to {end_date or 'Not specified'}")
            if stype_in:
                table.add_row("Symbol Type", stype_in)
            if dry_run:
                table.add_row("Mode", "🎭 DRY RUN")

            console.print(table)
            
        # Validate symbol and stype_in combination
        if symbols and stype_in:
            symbol_list = parse_symbols(symbols) if isinstance(symbols, str) else symbols
            validation_errors = validate_symbol_stype_combination(symbol_list, stype_in)
            
            if validation_errors:
                console.print("\n❌ [red]Symbol validation failed:[/red]")
                for error in validation_errors:
                    console.print(f"   • {error}")
                console.print("\n💡 [yellow]Symbol format guide:[/yellow]")
                console.print("   • Continuous: Use format like ES.c.0, NG.c.0")
                console.print("   • Parent: Use format like ES.FUT, NG.FUT")
                console.print("   • Native: Use format like SPY, AAPL")
                console.print("\n📖 See 'python main.py examples ingest' for more examples")
                raise typer.Exit(1)
        
        # If dry run, show what would happen and exit
        if dry_run:
            console.print("\n🎭 [bold yellow]DRY RUN MODE - No ingestion will be executed[/bold yellow]")
            console.print("\n📋 [cyan]What would happen:[/cyan]")
            console.print(f"  1. Initialize {api.upper()} API connection")
            console.print(f"  2. Validate API credentials and permissions")
            if job:
                console.print(f"  3. Load job configuration: {job}")
                console.print(f"  4. Apply any parameter overrides")
            else:
                console.print(f"  3. Query {schema} data from {dataset}")
                console.print(f"  4. Process symbols: {overrides.get('symbols', [])}")
            console.print(f"  5. Fetch data for date range")
            console.print(f"  6. Transform and validate records")
            console.print(f"  7. Store data in TimescaleDB")
            console.print(f"  8. Quarantine any failed records to dlq/")
            console.print("\n💡 [yellow]Remove --dry-run to execute the ingestion[/yellow]")
            raise typer.Exit(0)

        # Confirmation prompt (unless forced)
        if not force and not dry_run:
            confirm = typer.confirm("Continue with this configuration?")
            if not confirm:
                console.print("⏹️  [yellow]Operation cancelled by user[/yellow]")
                raise typer.Exit(0)

        # Execute pipeline
        console.print("⚙️  [green]Initializing pipeline orchestrator...[/green]")

        # Prepare job description for progress display
        if job:
            job_description = f"Ingesting {api.upper()} data - Job: {job}"
        else:
            symbols_str = ", ".join(symbols) if symbols else "specified symbols"
            job_description = f"Ingesting {api.upper()} {schema} data for {symbols_str}"

        with EnhancedProgress(
            job_description,
            show_speed=True,
            show_eta=True,
            show_records=True
        ) as progress:
            # Create progress callback for the orchestrator
            def progress_callback(**kwargs):
                description = kwargs.get('description', '')
                completed = kwargs.get('completed', 0)
                total = kwargs.get('total', 0)
                
                # Update main progress bar
                if total > 0:
                    progress.update_main(
                        completed=completed,
                        total=total,
                        description=description
                    )
                
                # Handle additional metrics
                if 'records_stored' in kwargs:
                    progress.update_metrics({
                        'records_stored': kwargs['records_stored'],
                        'records_quarantined': kwargs.get('records_quarantined', 0),
                        'chunks_processed': kwargs.get('chunks_processed', 0)
                    })
                
                # Handle stage updates
                if 'stage' in kwargs:
                    progress.update_stage(kwargs['stage'], description)
                
                # Handle errors
                if kwargs.get('error'):
                    progress.set_status(f"[red]Error: {description}[/red]")

            orchestrator = PipelineOrchestrator(progress_callback=progress_callback)
            success = orchestrator.execute_ingestion(
                api_type=api,
                job_name=job,
                overrides=overrides if overrides else None
            )

        if success:
            console.print("✅ [bold green]Pipeline completed successfully![/bold green]")

            # Display pipeline statistics
            stats = orchestrator.stats.to_dict()
            console.print("\n📊 [bold cyan]Pipeline Statistics:[/bold cyan]")

            stats_table = Table(show_header=True, header_style="bold magenta")
            stats_table.add_column("Metric")
            stats_table.add_column("Value")

            for key, value in stats.items():
                if value is not None:
                    stats_table.add_row(key.replace("_", " ").title(), str(value))

            console.print(stats_table)

        else:
            console.print("❌ [bold red]Pipeline failed. Check logs for details.[/bold red]")
            raise typer.Exit(1)

    except PipelineError as e:
        console.print(f"❌ [red]Pipeline error: {e}[/red]")
        
        # Show troubleshooting help
        CLITroubleshooter.show_help(str(e))
        
        console.print("\n💡 [yellow]Common causes:[/yellow]")
        console.print("   • API authentication issues - check DATABENTO_API_KEY")
        console.print("   • Invalid symbol or dataset")
        console.print("   • Date range has no available data")
        console.print("   • Network connectivity problems")
        console.print("\nUse 'python main.py troubleshoot' for more help")
        
        logger.error("Pipeline execution failed", error=str(e))
        raise typer.Exit(1)
        
    except typer.Exit:
        # Re-raise Exit exceptions without logging as errors
        raise
    except Exception as e:
        import traceback
        console.print(f"❌ [red]Unexpected error: {e}[/red]")
        console.print("\n🔧 [yellow]Troubleshooting:[/yellow]")
        console.print("   • Check logs for details: tail -f logs/app.log")
        console.print("   • Verify environment setup with 'python main.py status'")
        console.print("   • Run 'python main.py troubleshoot' for common issues")
        
        # Log full traceback for debugging
        logger.error(
            "Unexpected error in CLI", 
            error=str(e), 
            error_type=type(e).__name__,
            traceback=traceback.format_exc()
        )
        raise typer.Exit(1)


@app.command()
def list_jobs(
    api: str = typer.Option("databento", help="API type to list jobs for")
):
    """List all available predefined jobs for the specified API."""
    console.print(f"📋 [bold blue]Available jobs for {api.upper()}:[/bold blue]")

    try:
        orchestrator = PipelineOrchestrator()
        api_config = orchestrator.load_api_config(api)
        jobs = api_config.get("jobs", [])

        if not jobs:
            console.print("ℹ️  [yellow]No predefined jobs found[/yellow]")
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Job Name")
        table.add_column("Dataset")
        table.add_column("Schema")
        table.add_column("Symbols")
        table.add_column("Date Range")

        for job in jobs:
            symbols = job.get("symbols", [])
            symbol_str = ", ".join(symbols) if isinstance(symbols, list) else str(symbols)
            if len(symbol_str) > 30:
                symbol_str = symbol_str[:27] + "..."

            date_range = f"{job.get('start_date', 'N/A')} to {job.get('end_date', 'N/A')}"

            table.add_row(
                job.get("name", "Unnamed"),
                job.get("dataset", "N/A"),
                job.get("schema", "N/A"),
                symbol_str,
                date_range
            )

        console.print(table)

    except Exception as e:
        console.print(f"❌ [red]Failed to load jobs: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status():
    """Check system status and connectivity."""
    console.print("🔍 [bold blue]Checking system status...[/bold blue]")

    # Check database connectivity
    try:
        import psycopg2

        DB_USER = os.getenv('TIMESCALEDB_USER', 'postgres')
        DB_PASSWORD = os.getenv('TIMESCALEDB_PASSWORD', '')
        DB_HOST = os.getenv('TIMESCALEDB_HOST', 'localhost')
        DB_PORT = os.getenv('TIMESCALEDB_PORT', '5432')
        DB_NAME = os.getenv('TIMESCALEDB_DBNAME', 'hist_data')

        if not all([DB_USER, DB_PASSWORD, DB_NAME]):
            console.print("❌ [red]Database environment variables not set[/red]")
            raise typer.Exit(1)

        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        console.print("✅ [green]TimescaleDB connection: OK[/green]")
        conn.close()

    except Exception as e:
        console.print(f"❌ [red]TimescaleDB connection: FAILED ({e})[/red]")

    # Check API key availability
    databento_key = os.getenv('DATABENTO_API_KEY')
    if databento_key:
        console.print("✅ [green]Databento API key: Configured[/green]")
    else:
        console.print("❌ [red]Databento API key: Not configured[/red]")

    # Check log directory
    log_dir = Path("logs")
    if log_dir.exists():
        console.print("✅ [green]Log directory: OK[/green]")
    else:
        console.print("⚠️  [yellow]Log directory: Missing (will be created)[/yellow]")

    console.print("\n📊 [bold cyan]System Information:[/bold cyan]")
    info_table = Table(show_header=True, header_style="bold magenta")
    info_table.add_column("Component")
    info_table.add_column("Status")

    info_table.add_row("Python Version", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    info_table.add_row("Working Directory", str(Path.cwd()))
    info_table.add_row("Config Directory", str(Path("configs")))

    console.print(info_table)


@app.command()
def version():
    """Display version information."""
    console.print("🏷️  [bold blue]Historical Data Ingestor[/bold blue]")
    console.print("Version: 1.0.0-mvp")
    console.print("Build: Story 2.6 Implementation")
    console.print(f"Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    console.print(f"CLI Framework: Typer with Rich formatting")


@app.command()
def examples(
    command: Optional[str] = typer.Argument(
        None,
        help="Specific command to show examples for (ingest, query, status, list-jobs)"
    )
):
    """
    Show practical examples for CLI commands.
    
    Examples:
        python main.py examples              # Show all examples
        python main.py examples query        # Show query examples only
        python main.py examples ingest       # Show ingestion examples
    """
    show_examples(command)


@app.command()
def troubleshoot(
    error: Optional[str] = typer.Argument(
        None,
        help="Error message or keyword to get specific help"
    )
):
    """
    Get troubleshooting help for common issues.
    
    Examples:
        python main.py troubleshoot                    # Show common issues
        python main.py troubleshoot "database error"   # Get database help
        python main.py troubleshoot "symbol not found" # Symbol resolution help
    """
    if error:
        console.print(f"\n🔍 [bold cyan]Troubleshooting: {error}[/bold cyan]\n")
        CLITroubleshooter.show_help(error)
    else:
        console.print("\n🔧 [bold cyan]Common Issues and Solutions:[/bold cyan]\n")
        for _, issue_data in CLITroubleshooter.COMMON_ISSUES.items():
            console.print(f"[bold yellow]{issue_data['title']}:[/bold yellow]")
            console.print(f"  Error patterns: {', '.join(issue_data['error_patterns'][:2])}...")
            console.print(f"  Solution: {issue_data['solutions'][0]}")
            console.print()


@app.command()
def tips(
    category: Optional[str] = typer.Argument(
        None,
        help="Category of tips to show (performance, quality, efficiency, troubleshooting)"
    )
):
    """
    Show usage tips and best practices.
    
    Examples:
        python main.py tips                  # Show all tips
        python main.py tips performance      # Performance optimization tips
        python main.py tips troubleshooting  # Troubleshooting tips
    """
    show_tips(category)


@app.command()
def schemas():
    """
    Display available data schemas and their fields.
    
    Shows detailed information about each schema type including:
    - Schema name and description
    - Key fields and their meanings
    - Common use cases
    """
    console.print("\n📊 [bold cyan]Available Data Schemas[/bold cyan]\n")
    table = format_schema_help()
    console.print(table)
    console.print("\n💡 [yellow]Use --schema parameter with query or ingest commands[/yellow]")
    console.print("Example: python main.py query -s ES.c.0 --schema trades")


@app.command("help-menu")
def help_menu():
    """
    Launch interactive help menu system.
    
    Provides an interactive, navigable help system with categories:
    - Getting Started
    - Data Ingestion
    - Querying Data
    - Common Workflows
    - Troubleshooting
    - Reference
    """
    InteractiveHelpMenu.show_menu()


@app.command()
def quickstart():
    """
    Interactive setup wizard for new users.
    
    Guides you through:
    - Environment verification
    - Choosing data type
    - Selecting symbols
    - Setting date ranges
    - Generating ready-to-use commands
    """
    QuickstartWizard.run()


@app.command()
def workflows(
    workflow_name: Optional[str] = typer.Argument(
        None,
        help="Specific workflow to display (daily_analysis, historical_research, intraday_analysis)"
    )
):
    """
    Show complete workflow examples for common use cases.
    
    Available workflows:
    - daily_analysis: Daily market data analysis
    - historical_research: Collecting data for backtesting
    - intraday_analysis: High-frequency trades and quotes analysis
    
    Examples:
        python main.py workflows                    # List all workflows
        python main.py workflows daily_analysis     # Show specific workflow
    """
    WorkflowExamples.show_workflow(workflow_name)


@app.command()
def cheatsheet():
    """
    Display quick reference cheat sheet.
    
    Shows:
    - Common commands
    - Query shortcuts
    - Date format examples
    - Symbol format reference
    - Pro tips for efficient usage
    """
    CheatSheet.display()


@app.command("market-calendar")
def market_calendar(
    start_date: str = typer.Argument(..., help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Argument(..., help="End date (YYYY-MM-DD)"),
    exchange: str = typer.Option("NYSE", help="Exchange name (NYSE, NASDAQ, CME_Equity, CME_Energy, LSE, etc.)"),
    show_holidays: bool = typer.Option(False, "--holidays", help="Show individual holidays in the date range"),
    show_schedule: bool = typer.Option(False, "--schedule", help="Show market open/close schedule"),
    coverage_only: bool = typer.Option(False, "--coverage", help="Show only coverage summary"),
    list_exchanges: bool = typer.Option(False, "--list-exchanges", help="List all available exchanges")
):
    """
    Market calendar analysis and trading day validation.
    
    Analyzes date ranges for trading days, holidays, and market coverage using
    pandas-market-calendars for accurate exchange-aware scheduling.
    
    Examples:
        # Basic coverage analysis
        python main.py market-calendar 2024-01-01 2024-01-31
        
        # CME Energy calendar analysis with holidays
        python main.py market-calendar 2024-01-01 2024-01-31 --exchange CME_Energy --holidays
        
        # Show market schedule for specific dates
        python main.py market-calendar 2024-12-23 2024-12-27 --schedule
        
        # Quick coverage check for API cost estimation
        python main.py market-calendar 2024-01-01 2024-12-31 --coverage
        
        # List all available exchanges
        python main.py market-calendar 2024-01-01 2024-01-02 --list-exchanges
    """
    from cli.smart_validation import MarketCalendar, PANDAS_MARKET_CALENDARS_AVAILABLE
    from datetime import datetime
    
    try:
        # Handle listing exchanges
        if list_exchanges:
            console.print("\n📅 [bold cyan]Available Market Calendars:[/bold cyan]\n")
            if PANDAS_MARKET_CALENDARS_AVAILABLE:
                try:
                    available = pmc.get_calendar_names()
                    console.print("Exchange calendars available through pandas-market-calendars:")
                    for exchange_name in sorted(available):
                        console.print(f"  • {exchange_name}")
                    console.print(f"\nTotal: {len(available)} exchanges available")
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not list exchanges: {e}[/yellow]")
                    console.print("Common exchanges: NYSE, NASDAQ, CME_Equity, CME_Energy, LSE, TSX")
            else:
                console.print("[yellow]pandas-market-calendars not installed. Using fallback calendar.[/yellow]")
                console.print("Available: NYSE (default fallback)")
            return

        # Parse and validate dates
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            
            if start_dt >= end_dt:
                console.print("[red]Error: Start date must be before end date[/red]")
                raise typer.Exit(1)
                
        except ValueError as e:
            console.print(f"[red]Error: Invalid date format. Use YYYY-MM-DD. {e}[/red]")
            raise typer.Exit(1)

        # Create market calendar
        try:
            calendar = MarketCalendar(exchange)
            console.print(f"\n📅 [bold cyan]Market Calendar Analysis: {calendar.name}[/bold cyan]")
            console.print(f"Date Range: {start_date} to {end_date}")
            console.print(f"Exchange: {exchange}")
            
        except Exception as e:
            console.print(f"[red]Error: Could not create calendar for {exchange}: {e}[/red]")
            if PANDAS_MARKET_CALENDARS_AVAILABLE:
                console.print("Try --list-exchanges to see available options")
            raise typer.Exit(1)

        # Get basic date range analysis
        total_days = (end_dt - start_dt).days + 1
        trading_days = calendar.get_trading_days_count(start_dt, end_dt)
        
        if not coverage_only:
            console.print(f"\n📊 [bold]Summary:[/bold]")
        
        console.print(f"Total days: {total_days}")
        console.print(f"Trading days: {trading_days}")
        console.print(f"Non-trading days: {total_days - trading_days}")
        
        if total_days > 0:
            coverage_pct = (trading_days / total_days) * 100
            console.print(f"Trading day coverage: {coverage_pct:.1f}%")
            
            # Coverage-based feedback
            if coverage_pct < 20:
                console.print("[red]⚠️  Very low trading day coverage - consider adjusting date range[/red]")
            elif coverage_pct < 50:
                console.print("[yellow]⚠️  Low trading day coverage - may want to adjust date range[/yellow]")
            elif coverage_pct > 85:
                console.print("[green]✅ Excellent trading day coverage[/green]")
            else:
                console.print("[blue]ℹ️  Good trading day coverage[/blue]")

        if coverage_only:
            return

        # Show holidays if requested
        if show_holidays and PANDAS_MARKET_CALENDARS_AVAILABLE:
            try:
                holidays = calendar.get_holidays(start_dt, end_dt)
                if len(holidays) > 0:
                    console.print(f"\n🏖️  [bold]Holidays ({len(holidays)}):[/bold]")
                    for holiday in holidays:
                        # Format holiday date
                        holiday_str = holiday.strftime("%Y-%m-%d (%A)")
                        console.print(f"  • {holiday_str}")
                else:
                    console.print(f"\n🏖️  [bold]Holidays:[/bold] None in this date range")
            except Exception as e:
                console.print(f"[yellow]Could not retrieve holidays: {e}[/yellow]")

        # Show early closes
        try:
            early_closes = calendar.get_early_closes(start_dt, end_dt)
            if early_closes:
                console.print(f"\n🕐 [bold]Early Market Closes ({len(early_closes)}):[/bold]")
                for close_date, close_info in sorted(early_closes.items()):
                    date_str = close_date.strftime("%Y-%m-%d (%A)")
                    console.print(f"  • {date_str}: {close_info}")
            elif not coverage_only:
                console.print(f"\n🕐 [bold]Early Market Closes:[/bold] None in this date range")
        except Exception as e:
            console.print(f"[yellow]Could not retrieve early closes: {e}[/yellow]")

        # Show market schedule if requested  
        if show_schedule and PANDAS_MARKET_CALENDARS_AVAILABLE:
            try:
                schedule_df = calendar.get_schedule(start_dt, end_dt)
                if not schedule_df.empty:
                    console.print(f"\n🕐 [bold]Market Schedule (first 10 days):[/bold]")
                    
                    # Create table for schedule display
                    table = Table()
                    table.add_column("Date", style="cyan")
                    table.add_column("Market Open", style="green")
                    table.add_column("Market Close", style="red")
                    
                    # Show first 10 days to avoid overwhelming output
                    for idx, (date, row) in enumerate(schedule_df.head(10).iterrows()):
                        if hasattr(row, 'market_open') and hasattr(row, 'market_close'):
                            open_time = row.market_open.strftime("%H:%M") if row.market_open is not None else "N/A"
                            close_time = row.market_close.strftime("%H:%M") if row.market_close is not None else "N/A" 
                        else:
                            open_time = "N/A"
                            close_time = "N/A"
                        
                        date_str = date.strftime("%Y-%m-%d (%a)")
                        table.add_row(date_str, open_time, close_time)
                    
                    console.print(table)
                    
                    if len(schedule_df) > 10:
                        console.print(f"... and {len(schedule_df) - 10} more trading days")
                else:
                    console.print(f"\n🕐 [bold]Market Schedule:[/bold] No trading days in this range")
            except Exception as e:
                console.print(f"[yellow]Could not retrieve market schedule: {e}[/yellow]")

        # API cost estimation
        if not coverage_only:
            console.print(f"\n💰 [bold]API Cost Estimation:[/bold]")
            if coverage_pct < 50:
                savings_pct = (100 - coverage_pct) / 100 * 100
                console.print(f"Potential API cost savings: ~{savings_pct:.0f}% by filtering non-trading days")
            else:
                console.print("Good date range efficiency for API usage")
                
        console.print(f"\n✅ [green]Analysis complete for {exchange} exchange[/green]")
        
    except Exception as e:
        console.print(f"[red]Error during market calendar analysis: {e}[/red]")
        logger.error(f"Market calendar command failed: {e}", exc_info=True)
        raise typer.Exit(1)


@app.command("exchange-mapping")
def exchange_mapping(
    symbols: Optional[str] = typer.Argument(None, help="Comma-separated symbols to analyze (optional)"),
    list_exchanges: bool = typer.Option(False, "--list", help="List all supported exchanges"),
    show_mappings: bool = typer.Option(False, "--mappings", help="Show all mapping rules"),
    exchange_info: Optional[str] = typer.Option(None, "--info", help="Get detailed info about a specific exchange"),
    test_symbol: Optional[str] = typer.Option(None, "--test", help="Test mapping for a single symbol"),
    confidence_threshold: float = typer.Option(0.0, "--min-confidence", help="Minimum confidence threshold for results")
):
    """
    Intelligent symbol-to-exchange mapping analysis and testing.
    
    Analyzes financial symbols and automatically determines the most appropriate
    market calendar exchange. Useful for understanding how the system maps symbols
    and for debugging exchange detection issues.
    
    Examples:
        # Analyze multiple symbols
        python main.py exchange-mapping "ES.FUT,CL.c.0,SPY,AAPL"
        
        # Test individual symbol mapping
        python main.py exchange-mapping --test "NG.FUT"
        
        # List all supported exchanges
        python main.py exchange-mapping --list
        
        # Get detailed exchange information
        python main.py exchange-mapping --info CME_Energy
        
        # Show all mapping rules
        python main.py exchange-mapping --mappings
        
        # Filter results by confidence
        python main.py exchange-mapping "SPY,UNKNOWN" --min-confidence 0.8
    """
    from cli.exchange_mapping import get_exchange_mapper
    
    try:
        mapper = get_exchange_mapper()
        
        # Handle listing all exchanges
        if list_exchanges:
            console.print("\n🏛️  [bold cyan]Supported Exchange Calendars:[/bold cyan]\n")
            
            exchanges = set()
            for mapping in mapper.mappings:
                exchanges.add(mapping.exchange)
            
            for exchange in sorted(exchanges):
                info = mapper.get_exchange_info(exchange)
                console.print(f"📊 [bold]{exchange}[/bold]")
                console.print(f"   Name: {info['name']}")
                console.print(f"   Region: {info['region']}")
                console.print(f"   Asset Classes: {', '.join(info['asset_classes'])}")
                console.print(f"   Trading Hours: {info['trading_hours']}")
                
                # Show example symbols
                examples = mapper.suggest_symbols_for_exchange(exchange, 3)
                if examples:
                    console.print(f"   Examples: {', '.join(examples)}")
                console.print()
            
            console.print(f"Total: {len(exchanges)} exchange calendars supported")
            return

        # Handle exchange info request
        if exchange_info:
            console.print(f"\n🏛️  [bold cyan]Exchange Information: {exchange_info}[/bold cyan]\n")
            
            info = mapper.get_exchange_info(exchange_info)
            console.print(f"[bold]Name:[/bold] {info['name']}")
            console.print(f"[bold]Region:[/bold] {info['region']}")
            console.print(f"[bold]Asset Classes:[/bold] {', '.join(info['asset_classes'])}")
            console.print(f"[bold]Trading Hours:[/bold] {info['trading_hours']}")
            console.print(f"[bold]Holidays:[/bold] {info['holidays']}")
            
            # Show example symbols for this exchange
            examples = mapper.suggest_symbols_for_exchange(exchange_info, 10)
            if examples:
                console.print(f"\n[bold]Example Symbols:[/bold]")
                for example in examples:
                    console.print(f"  • {example}")
            
            # Show mapping rules for this exchange
            console.print(f"\n[bold]Mapping Rules:[/bold]")
            rules_count = 0
            for mapping in mapper.mappings:
                if mapping.exchange == exchange_info:
                    console.print(f"  • {mapping.description} (confidence: {mapping.confidence:.2f})")
                    rules_count += 1
            
            if rules_count == 0:
                console.print("  No specific mapping rules found")
            
            return

        # Handle showing all mapping rules
        if show_mappings:
            console.print("\n📋 [bold cyan]All Symbol Mapping Rules:[/bold cyan]\n")
            
            current_exchange = None
            for mapping in mapper.mappings:
                if mapping.exchange != current_exchange:
                    current_exchange = mapping.exchange
                    console.print(f"\n🏛️  [bold]{current_exchange}[/bold]")
                
                console.print(f"   📊 {mapping.description}")
                console.print(f"      Confidence: {mapping.confidence:.2f}")
                console.print(f"      Asset Class: {mapping.asset_class.value}")
                console.print(f"      Pattern: {mapping.pattern}")
                if mapping.examples:
                    console.print(f"      Examples: {', '.join(mapping.examples[:3])}")
                console.print()
            
            return

        # Handle single symbol testing
        if test_symbol:
            console.print(f"\n🔍 [bold cyan]Testing Symbol: {test_symbol}[/bold cyan]\n")
            
            exchange, confidence, mapping_info = mapper.map_symbol_to_exchange(test_symbol)
            
            console.print(f"[bold]Result:[/bold] {exchange}")
            console.print(f"[bold]Confidence:[/bold] {confidence:.2f}")
            
            if mapping_info:
                console.print(f"[bold]Matched Rule:[/bold] {mapping_info.description}")
                console.print(f"[bold]Asset Class:[/bold] {mapping_info.asset_class.value}")
                console.print(f"[bold]Region:[/bold] {mapping_info.region.value}")
                console.print(f"[bold]Pattern:[/bold] {mapping_info.pattern}")
            else:
                console.print("[yellow]No specific rule matched - using fallback[/yellow]")
            
            # Validate the mapping
            is_valid, reason = mapper.validate_symbol_exchange_pair(test_symbol, exchange)
            if is_valid:
                console.print(f"[green]✅ {reason}[/green]")
            else:
                console.print(f"[red]❌ {reason}[/red]")
            
            return

        # Handle symbol analysis
        if symbols:
            symbol_list = [s.strip() for s in symbols.split(',')]
            console.print(f"\n🎯 [bold cyan]Symbol Exchange Mapping Analysis[/bold cyan]")
            console.print(f"Analyzing {len(symbol_list)} symbols...\n")
            
            # Create results table
            table = Table()
            table.add_column("Symbol", style="cyan")
            table.add_column("Exchange", style="green") 
            table.add_column("Confidence", style="yellow")
            table.add_column("Asset Class", style="blue")
            table.add_column("Description", style="white")
            
            all_mappings = {}
            for symbol in symbol_list:
                exchange, confidence, mapping_info = mapper.map_symbol_to_exchange(symbol)
                
                # Apply confidence filter
                if confidence < confidence_threshold:
                    continue
                    
                asset_class = mapping_info.asset_class.value if mapping_info else "unknown"
                description = mapping_info.description if mapping_info else "fallback mapping"
                
                # Color code confidence
                if confidence >= 0.9:
                    conf_display = f"[green]{confidence:.2f}[/green]"
                elif confidence >= 0.7:
                    conf_display = f"[yellow]{confidence:.2f}[/yellow]"
                else:
                    conf_display = f"[red]{confidence:.2f}[/red]"
                
                table.add_row(symbol, exchange, conf_display, asset_class, description)
                all_mappings[symbol] = (exchange, confidence, mapping_info)
            
            console.print(table)
            
            # Group analysis
            if len(symbol_list) > 1:
                console.print(f"\n📊 [bold]Group Analysis:[/bold]")
                group_exchange, group_confidence, group_mappings = mapper.map_symbols_to_exchange(symbol_list)
                console.print(f"Best group exchange: {group_exchange}")
                console.print(f"Average confidence: {group_confidence:.2f}")
                
                # Show exchange distribution
                exchange_counts = {}
                for symbol, (exchange, conf, mapping) in all_mappings.items():
                    if conf >= confidence_threshold:
                        exchange_counts[exchange] = exchange_counts.get(exchange, 0) + 1
                
                if exchange_counts:
                    console.print(f"\nExchange distribution:")
                    for exchange, count in sorted(exchange_counts.items(), key=lambda x: x[1], reverse=True):
                        percentage = (count / len([m for m in all_mappings.values() if m[1] >= confidence_threshold])) * 100
                        console.print(f"  • {exchange}: {count} symbols ({percentage:.1f}%)")
            
            return

        # No arguments provided - show usage
        console.print("\n🎯 [bold cyan]Exchange Mapping Tool[/bold cyan]")
        console.print("\nThis tool helps analyze and test intelligent symbol-to-exchange mapping.")
        console.print("\n[bold]Quick Examples:[/bold]")
        console.print("  python main.py exchange-mapping \"ES.FUT,SPY\"")
        console.print("  python main.py exchange-mapping --test CL.c.0")
        console.print("  python main.py exchange-mapping --list")
        console.print("  python main.py exchange-mapping --info CME_Energy")
        console.print("\nUse --help for full documentation")
        
    except Exception as e:
        console.print(f"[red]Error during exchange mapping analysis: {e}[/red]")
        logger.error(f"Exchange mapping command failed: {e}", exc_info=True)
        raise typer.Exit(1)


@app.command()
def backfill(
    symbol_group: str = typer.Argument(..., help="Symbol group: SP500_SAMPLE, ENERGY_FUTURES, INDEX_FUTURES, or custom symbols"),
    lookback: str = typer.Option("1y", help="Lookback period: 1d, 1w, 1m, 3m, 6m, 1y, 3y, 5y, 10y"),
    schemas: List[str] = typer.Option(["ohlcv-1d"], help="Data schemas to backfill"),
    api: str = typer.Option("databento", help="API provider"),
    dataset: str = typer.Option("GLBX.MDP3", help="Dataset to use"),
    batch_size: int = typer.Option(5, help="Number of symbols to process in parallel"),
    retry_failed: bool = typer.Option(True, help="Automatically retry failed symbols"),
    dry_run: bool = typer.Option(False, help="Preview operation without execution"),
    force: bool = typer.Option(False, help="Skip confirmation prompts")
):
    """
    High-level backfill command for common use cases.
    
    This command simplifies bulk data ingestion by providing shortcuts for 
    common symbol groups and automatic date range calculation.
    
    Examples:
        # Backfill S&P 500 sample daily data for last year
        python main.py backfill SP500_SAMPLE --lookback 1y
        
        # Backfill energy futures with multiple schemas
        python main.py backfill ENERGY_FUTURES --schemas ohlcv-1d --lookback 6m
        
        # Custom symbol list with specific parameters
        python main.py backfill "ES.c.0,NQ.c.0,CL.c.0" --lookback 3m --batch-size 3
        
        # Preview operation without execution
        python main.py backfill INDEX_FUTURES --dry-run
    """
    from datetime import datetime, timedelta
    
    try:
        console.print("🚀 [bold cyan]HDI Backfill Operation[/bold cyan]")
        
        # Initialize symbol group manager
        group_manager = SymbolGroupManager()
        
        # Resolve symbols
        console.print(f"\n🔍 Resolving symbol group: [cyan]{symbol_group}[/cyan]")
        
        try:
            symbols = group_manager.resolve_group(symbol_group)
        except ValueError as e:
            console.print(f"❌ [red]Error resolving symbol group: {e}[/red]")
            
            # Show available groups as help
            console.print("\n💡 [yellow]Available symbol groups:[/yellow]")
            group_manager.display_group_table()
            raise typer.Exit(1)
        
        console.print(f"✅ Resolved to [green]{len(symbols)}[/green] symbols: {', '.join(symbols[:5])}")
        if len(symbols) > 5:
            console.print(f"   ... and {len(symbols) - 5} more")
        
        # Calculate date range from lookback
        end_date = datetime.now().date()
        
        # Parse lookback period
        lookback_mapping = {
            '1d': timedelta(days=1),
            '1w': timedelta(weeks=1),
            '1m': timedelta(days=30),
            '3m': timedelta(days=90),
            '6m': timedelta(days=180),
            '1y': timedelta(days=365),
            '3y': timedelta(days=365*3),
            '5y': timedelta(days=365*5),
            '10y': timedelta(days=365*10)
        }
        
        if lookback not in lookback_mapping:
            console.print(f"❌ [red]Invalid lookback period: {lookback}[/red]")
            console.print("Valid options: " + ", ".join(lookback_mapping.keys()))
            raise typer.Exit(1)
            
        start_date = end_date - lookback_mapping[lookback]
        
        # Validate schemas
        valid_schemas = ["ohlcv-1d", "ohlcv-1h", "trades", "tbbo", "statistics", "definition"]
        for schema in schemas:
            if schema not in valid_schemas:
                console.print(f"❌ [red]Invalid schema: {schema}[/red]")
                console.print("Valid schemas: " + ", ".join(valid_schemas))
                raise typer.Exit(1)
        
        # Calculate scope and estimates
        total_operations = len(symbols) * len(schemas)
        estimated_time_per_symbol = 30  # seconds per symbol per schema
        estimated_total_time = (total_operations * estimated_time_per_symbol) / batch_size
        
        # Display operation summary
        console.print("\n📋 [bold cyan]Backfill Operation Summary[/bold cyan]")
        
        summary_table = Table(show_header=True, header_style="bold magenta")
        summary_table.add_column("Parameter", style="cyan")
        summary_table.add_column("Value", style="green")
        
        summary_table.add_row("Symbol Group", symbol_group)
        summary_table.add_row("Symbols Count", f"{len(symbols)} symbols")
        summary_table.add_row("Date Range", f"{start_date} to {end_date}")
        summary_table.add_row("Lookback Period", lookback)
        summary_table.add_row("Schemas", ", ".join(schemas))
        summary_table.add_row("API Provider", api)
        summary_table.add_row("Dataset", dataset)
        summary_table.add_row("Total Operations", str(total_operations))
        summary_table.add_row("Batch Size", f"{batch_size} parallel")
        summary_table.add_row("Estimated Time", f"{estimated_total_time/60:.1f} minutes")
        
        console.print(summary_table)
        
        # Show first few symbols
        if len(symbols) > 0:
            console.print(f"\n📊 [bold blue]Symbols to process:[/bold blue]")
            symbol_display = symbols[:10]
            if len(symbols) > 10:
                symbol_display.append(f"... and {len(symbols) - 10} more")
            console.print("   " + ", ".join(symbol_display))
        
        if dry_run:
            console.print("\n🎭 [yellow]DRY RUN MODE - No operations will be executed[/yellow]")
            console.print("\n✅ [green]Operation plan validated successfully![/green]")
            console.print("\n💡 [dim]Remove --dry-run to execute the backfill[/dim]")
            return
        
        # Confirmation prompt (unless forced)
        if not force:
            console.print(f"\n⚠️  [yellow]This will execute {total_operations} ingestion operations[/yellow]")
            confirm = typer.confirm("Continue with backfill?")
            if not confirm:
                console.print("⏹️  [yellow]Operation cancelled by user[/yellow]")
                raise typer.Exit(0)
        
        # Execute backfill operations
        console.print("\n🚀 [bold green]Starting backfill operations...[/bold green]")
        
        # Process symbols in batches
        import math
        total_batches = math.ceil(len(symbols) / batch_size)
        
        with EnhancedProgress(
            f"Backfilling {len(symbols)} symbols across {len(schemas)} schemas",
            show_speed=True,
            show_eta=True,
            show_records=True,
            use_adaptive_eta=True
        ) as progress:
            
            successful_operations = 0
            failed_operations = 0
            
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(symbols))
                batch_symbols = symbols[start_idx:end_idx]
                
                console.print(f"\n📦 Processing batch {batch_idx + 1}/{total_batches}: {', '.join(batch_symbols)}")
                
                # Process each symbol in the batch
                for symbol in batch_symbols:
                    for schema in schemas:
                        operation_num = (batch_idx * batch_size * len(schemas) + 
                                       batch_symbols.index(symbol) * len(schemas) + 
                                       schemas.index(schema) + 1)
                        
                        progress.update_main(
                            completed=operation_num - 1,
                            total=total_operations,
                            description=f"Processing {symbol} ({schema})",
                            operation_type=f"backfill_{schema}"
                        )
                        
                        # Build overrides for this operation
                        overrides = {
                            'dataset': dataset,
                            'schema': schema,
                            'symbols': [symbol],
                            'start_date': start_date.isoformat(),
                            'end_date': end_date.isoformat(),
                            'stype_in': 'parent',
                            'name': f"backfill_{schema}_{symbol}".replace('.', '_')
                        }
                        
                        try:
                            # Execute ingestion
                            orchestrator = PipelineOrchestrator()
                            success = orchestrator.execute_ingestion(
                                api_type=api,
                                job_name=None,
                                overrides=overrides
                            )
                            
                            if success:
                                successful_operations += 1
                                progress.log(f"✅ {symbol} ({schema}) completed", style="green")
                            else:
                                failed_operations += 1
                                progress.log(f"❌ {symbol} ({schema}) failed", style="red")
                                
                                if not retry_failed:
                                    continue
                                    
                                # Retry once
                                progress.log(f"🔄 Retrying {symbol} ({schema})", style="yellow")
                                success = orchestrator.execute_ingestion(
                                    api_type=api,
                                    job_name=None,
                                    overrides=overrides
                                )
                                
                                if success:
                                    successful_operations += 1
                                    failed_operations -= 1
                                    progress.log(f"✅ {symbol} ({schema}) retry succeeded", style="green")
                                else:
                                    progress.log(f"❌ {symbol} ({schema}) retry failed", style="red")
                        
                        except Exception as e:
                            failed_operations += 1
                            progress.log(f"❌ {symbol} ({schema}) error: {str(e)[:50]}", style="red")
            
            # Final progress update
            progress.update_main(
                completed=total_operations,
                total=total_operations,
                description="Backfill completed!"
            )
        
        # Display final results
        console.print("\n📊 [bold cyan]Backfill Results:[/bold cyan]")
        
        results_table = Table(show_header=True, header_style="bold magenta")
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Count", style="bold")
        results_table.add_column("Percentage", style="green")
        
        success_rate = (successful_operations / total_operations * 100) if total_operations > 0 else 0
        failure_rate = (failed_operations / total_operations * 100) if total_operations > 0 else 0
        
        results_table.add_row("✅ Successful", str(successful_operations), f"{success_rate:.1f}%")
        results_table.add_row("❌ Failed", str(failed_operations), f"{failure_rate:.1f}%")
        results_table.add_row("📊 Total", str(total_operations), "100.0%")
        
        console.print(results_table)
        
        if successful_operations == total_operations:
            console.print("\n🎉 [bold green]All operations completed successfully![/bold green]")
        elif successful_operations > 0:
            console.print(f"\n⚠️  [yellow]Completed with {failed_operations} failures[/yellow]")
            console.print("💡 [dim]Check logs for detailed error information[/dim]")
        else:
            console.print("\n❌ [bold red]All operations failed[/bold red]")
            console.print("💡 [dim]Check your configuration and try again[/dim]")
            raise typer.Exit(1)
            
    except KeyboardInterrupt:
        console.print("\n\n⏹️  [yellow]Operation cancelled by user[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n❌ [red]Backfill failed: {e}[/red]")
        logger.error("Backfill operation failed", error=str(e), error_type=type(e).__name__)
        raise typer.Exit(1)


@app.command()
def groups(
    list_all: bool = typer.Option(False, "--list", "-l", help="List all available symbol groups"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    info: Optional[str] = typer.Option(None, "--info", "-i", help="Show detailed info for a specific group"),
    create: Optional[str] = typer.Option(None, "--create", help="Create a new custom group"),
    symbols_input: Optional[str] = typer.Option(None, "--symbols", help="Symbols for new group (comma-separated)"),
    description: Optional[str] = typer.Option(None, "--description", help="Description for new group"),
    delete: Optional[str] = typer.Option(None, "--delete", help="Delete a custom group")
):
    """
    Manage symbol groups for batch operations.
    
    Symbol groups allow you to organize collections of symbols for easy
    batch processing with the backfill command.
    
    Examples:
        python main.py groups --list                           # List all groups
        python main.py groups --category commodities           # Show commodity groups
        python main.py groups --info SP500_SAMPLE              # Show group details
        python main.py groups --create MY_PORTFOLIO \\
          --symbols "AAPL,MSFT,GOOGL" --description "My portfolio"
    """
    group_manager = SymbolGroupManager()
    
    try:
        if create:
            # Create new custom group
            if not symbols_input:
                console.print("❌ [red]--symbols is required when creating a group[/red]")
                raise typer.Exit(1)
            
            symbols = [s.strip().upper() for s in symbols_input.split(',')]
            
            # Validate symbols
            validation = group_manager.validate_symbols(symbols)
            
            if validation['invalid_symbols']:
                console.print(f"⚠️  [yellow]Warning: {len(validation['invalid_symbols'])} invalid symbols will be skipped[/yellow]")
                console.print(f"Invalid: {', '.join(validation['invalid_symbols'])}")
            
            if validation['duplicates_removed'] > 0:
                console.print(f"ℹ️  [blue]Removed {validation['duplicates_removed']} duplicate symbols[/blue]")
            
            if not validation['valid_symbols']:
                console.print("❌ [red]No valid symbols provided[/red]")
                raise typer.Exit(1)
            
            group_manager.create_custom_group(
                name=create,
                symbols=validation['valid_symbols'],
                description=description or f"Custom group with {len(validation['valid_symbols'])} symbols"
            )
            
        elif delete:
            # Delete custom group
            group_manager.delete_custom_group(delete)
            
        elif info:
            # Show detailed group info
            group_info = group_manager.get_group_info(info)
            if not group_info:
                console.print(f"❌ [red]Group '{info}' not found[/red]")
                raise typer.Exit(1)
            
            console.print(f"\n📊 [bold blue]Group Details: {group_info['name']}[/bold blue]")
            
            info_table = Table(show_header=False, box=None)
            info_table.add_column("Property", style="cyan")
            info_table.add_column("Value", style="bold")
            
            info_table.add_row("Name", group_info['name'])
            info_table.add_row("Type", group_info['type'].title())
            info_table.add_row("Category", group_info.get('category', 'N/A'))
            info_table.add_row("Description", group_info.get('description', 'N/A'))
            info_table.add_row("Symbol Count", str(group_info['symbol_count']))
            
            if group_info.get('created_at'):
                info_table.add_row("Created", group_info['created_at'][:10])
            if group_info.get('last_updated'):
                info_table.add_row("Last Updated", group_info['last_updated'][:10])
            
            console.print(info_table)
            
            # Show symbols
            console.print(f"\n📈 [bold blue]Symbols ({group_info['symbol_count']}):[/bold blue]")
            symbols = group_info['symbols']
            
            # Display symbols in rows of 8
            for i in range(0, len(symbols), 8):
                row_symbols = symbols[i:i+8]
                console.print("  " + "  ".join(f"[green]{s}[/green]" for s in row_symbols))
            
        else:
            # List groups (default action)
            if list_all or category or (not create and not delete and not info):
                if category:
                    console.print(f"📊 [bold blue]Symbol Groups - Category: {category}[/bold blue]")
                else:
                    console.print("📊 [bold blue]All Available Symbol Groups[/bold blue]")
                
                all_groups = group_manager.list_groups(category=category)
                
                if not all_groups['predefined'] and not all_groups['custom']:
                    console.print("ℹ️  [yellow]No groups found[/yellow]")
                    return
                
                group_manager.display_group_table()
                
                # Show categories
                categories = group_manager.get_categories()
                console.print(f"\n🏷️  [bold blue]Available Categories:[/bold blue]")
                console.print("  " + "  ".join(f"[yellow]{cat}[/yellow]" for cat in sorted(categories)))
                
                console.print(f"\n💡 [dim]Use 'python main.py groups --info GROUP_NAME' for details[/dim]")
                console.print(f"💡 [dim]Use 'python main.py backfill GROUP_NAME' to process a group[/dim]")
            
    except Exception as e:
        console.print(f"❌ [red]Groups operation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def symbols(
    category: Optional[str] = typer.Option(
        None,
        "--category", "-c",
        help="Filter by category (e.g., 'Energy', 'Metals', 'Currencies')"
    ),
    search: Optional[str] = typer.Option(
        None,
        "--search", "-s",
        help="Search for symbols by name or code"
    )
):
    """
    Symbol discovery and reference tool.
    
    Browse available symbols by category or search by name.
    
    Examples:
        python main.py symbols                      # Show all categories
        python main.py symbols --category Energy    # Show energy symbols
        python main.py symbols --search oil         # Search for oil-related symbols
    """
    SymbolHelper.show_symbols(category=category, search=search)


@app.command()
def validate(
    input_value: str = typer.Argument(..., help="Value to validate"),
    input_type: str = typer.Option(
        "symbol",
        "--type", "-t",
        help="Type of validation: symbol, symbol_list, schema, date"
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Enable interactive suggestions"
    ),
    start_date: Optional[str] = typer.Option(
        None,
        "--start-date",
        help="Start date for date range validation (YYYY-MM-DD)"
    ),
    end_date: Optional[str] = typer.Option(
        None,
        "--end-date", 
        help="End date for date range validation (YYYY-MM-DD)"
    )
):
    """
    🔍 Smart validation for CLI inputs with suggestions and autocomplete.
    
    Validate symbols, schemas, dates, and other inputs with intelligent
    error messages and helpful suggestions.
    
    Examples:
        python main.py validate ES.c.0                           # Validate symbol
        python main.py validate "ES.c.0,NQ.c.0" --type symbol_list  # Validate symbol list
        python main.py validate ohlcv-1d --type schema              # Validate schema
        python main.py validate "" --type date_range --start-date 2024-01-01 --end-date 2024-12-31
    """
    console.print(f"\n🔍 [bold cyan]Validating {input_type}: {input_value}[/bold cyan]\n")
    
    try:
        if input_type == "date_range":
            if not start_date or not end_date:
                console.print("❌ [red]Date range validation requires --start-date and --end-date[/red]")
                raise typer.Exit(1)
            result = validate_cli_input(
                input_value, input_type, 
                start_date=start_date, 
                end_date=end_date,
                interactive=interactive
            )
        else:
            result = validate_cli_input(input_value, input_type, interactive=interactive)
            
        # Create validator instance to show results
        validator = create_smart_validator()
        validator.show_validation_result(result, f"{input_type.title()} Validation")
        
        if result.is_valid:
            console.print("\n✅ [bold green]Validation passed![/bold green]")
        else:
            console.print(f"\n❌ [bold red]Validation failed![/bold red]")
            if result.suggestions:
                console.print("\n💡 [yellow]Try one of the suggestions above[/yellow]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"❌ [red]Validation error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def workflow(
    action: str = typer.Argument(
        ...,
        help="Action: create, list, load, run"
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name", "-n",
        help="Workflow name for load/run actions"
    ),
    workflow_type: Optional[str] = typer.Option(
        None,
        "--type", "-t",
        help="Workflow type: backfill, daily_update, multi_symbol, data_quality, custom"
    )
):
    """
    🔧 Interactive workflow builder for complex operations.
    
    Create, manage, and execute complex data processing workflows
    with step-by-step guidance and intelligent validation.
    
    Examples:
        python main.py workflow create                    # Create workflow interactively
        python main.py workflow create --type backfill   # Create specific workflow type
        python main.py workflow list                     # Show saved workflows
        python main.py workflow load --name "My Workflow"  # Load specific workflow
    """
    if action == "create":
        console.print("\n🔧 [bold cyan]Creating Interactive Workflow[/bold cyan]\n")
        
        workflow_type_enum = None
        if workflow_type:
            from cli.interactive_workflows import WorkflowType
            try:
                workflow_type_enum = WorkflowType(workflow_type.lower())
            except ValueError:
                console.print(f"❌ [red]Invalid workflow type: {workflow_type}[/red]")
                console.print("Valid types: backfill, daily_update, multi_symbol, data_quality, custom")
                raise typer.Exit(1)
        
        try:
            workflow = create_interactive_workflow()
            if workflow:
                console.print(f"\n✅ [bold green]Workflow '{workflow.name}' created successfully![/bold green]")
                console.print(f"📋 Type: {workflow.workflow_type.value}")
                console.print(f"📝 Steps: {len(workflow.steps)}")
                console.print(f"💾 ID: {workflow.id}")
            else:
                console.print("\n⏹️  [yellow]Workflow creation cancelled[/yellow]")
        except Exception as e:
            console.print(f"❌ [red]Failed to create workflow: {e}[/red]")
            raise typer.Exit(1)
            
    elif action == "list":
        console.print("\n📋 [bold cyan]Saved Workflows[/bold cyan]\n")
        list_saved_workflows()
        
    elif action == "load":
        if not name:
            console.print("❌ [red]Workflow name required for load action[/red]")
            console.print("Use: python main.py workflow load --name 'Workflow Name'")
            raise typer.Exit(1)
            
        try:
            workflow = load_workflow_by_name(name)
            if workflow:
                console.print(f"\n✅ [bold green]Loaded workflow: {workflow.name}[/bold green]")
                console.print(f"📋 Type: {workflow.workflow_type.value}")
                console.print(f"📝 Description: {workflow.description}")
                console.print(f"🔧 Steps: {len(workflow.steps)}")
                
                # Show workflow steps
                console.print("\n📋 [cyan]Workflow Steps:[/cyan]")
                for i, step in enumerate(workflow.steps, 1):
                    console.print(f"  {i}. {step.name} ({step.step_type})")
                    console.print(f"     {step.description}")
                    
            else:
                console.print(f"❌ [red]Workflow '{name}' not found[/red]")
                console.print("\nAvailable workflows:")
                list_saved_workflows()
                raise typer.Exit(1)
        except Exception as e:
            console.print(f"❌ [red]Failed to load workflow: {e}[/red]")
            raise typer.Exit(1)
            
    elif action == "run":
        console.print("🚀 [yellow]Workflow execution not yet implemented[/yellow]")
        console.print("This feature will execute saved workflows automatically.")
        
    else:
        console.print(f"❌ [red]Unknown action: {action}[/red]")
        console.print("Valid actions: create, list, load, run")
        raise typer.Exit(1)


@app.command() 
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
        help="Number of suggestions to show"
    )
):
    """
    🔍 Advanced symbol lookup with autocomplete and suggestions.
    
    Look up symbols with intelligent fuzzy matching and detailed
    information including asset class, sector, and trading status.
    
    Examples:
        python main.py symbol-lookup ES.c.0           # Exact lookup
        python main.py symbol-lookup ESX --fuzzy      # Fuzzy search
        python main.py symbol-lookup APPL --fuzzy --suggestions 10  # More suggestions
    """
    console.print(f"\n🔍 [bold cyan]Symbol Lookup: {symbol}[/bold cyan]\n")
    
    try:
        validator = create_smart_validator()
        result = validator.validate_symbol(symbol, interactive=False)
        
        if result.is_valid:
            console.print("✅ [bold green]Valid Symbol Found[/bold green]")
            
            # Show symbol information
            if result.metadata:
                info_table = Table(show_header=True, header_style="bold magenta")
                info_table.add_column("Property", style="cyan")
                info_table.add_column("Value", style="green")
                
                for key, value in result.metadata.items():
                    if key != "symbol":
                        formatted_key = key.replace('_', ' ').title()
                        info_table.add_row(formatted_key, str(value))
                        
                console.print(info_table)
                
        else:
            console.print(f"❌ [red]Symbol not found: {symbol}[/red]")
            
            if fuzzy and result.suggestions:
                console.print(f"\n💡 [yellow]Similar symbols found:[/yellow]\n")
                
                suggestions_table = Table(show_header=True, header_style="bold magenta")
                suggestions_table.add_column("Symbol", style="green")
                suggestions_table.add_column("Asset Class", style="cyan")
                suggestions_table.add_column("Sector", style="dim")
                
                for suggestion in result.suggestions[:suggestions]:
                    symbol_info = validator.symbol_cache.get_symbol_info(suggestion)
                    asset_class = symbol_info.get('asset_class', 'Unknown') if symbol_info else 'Unknown'
                    sector = symbol_info.get('sector', 'Unknown') if symbol_info else 'Unknown'
                    suggestions_table.add_row(suggestion, asset_class, sector)
                    
                console.print(suggestions_table)
            else:
                console.print("\n💡 [yellow]Try using --fuzzy for similar symbols[/yellow]")
                
    except Exception as e:
        console.print(f"❌ [red]Symbol lookup error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def market_calendar(
    start_date: str = typer.Argument(..., help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Argument(..., help="End date (YYYY-MM-DD)"),
    symbol: Optional[str] = typer.Option(
        None,
        "--symbol", "-s",
        help="Symbol for asset-specific calendar"
    )
):
    """
    📅 Market calendar analysis with trading day calculations.
    
    Analyze date ranges for trading days, holidays, and market sessions
    with intelligent calendar awareness.
    
    Examples:
        python main.py market-calendar 2024-01-01 2024-01-31        # January trading days
        python main.py market-calendar 2024-12-20 2024-12-31 --symbol ES.c.0  # Year-end futures
    """
    console.print(f"\n📅 [bold cyan]Market Calendar Analysis[/bold cyan]\n")
    console.print(f"📊 Date Range: {start_date} to {end_date}")
    if symbol:
        console.print(f"🎯 Symbol: {symbol}")
    console.print()
    
    try:
        validator = create_smart_validator()
        result = validator.validate_date_range(start_date, end_date, symbol, interactive=False)
        
        if result.is_valid:
            analysis = result.metadata
            
            # Create analysis table
            calendar_table = Table(show_header=True, header_style="bold magenta")
            calendar_table.add_column("Metric", style="cyan")
            calendar_table.add_column("Value", style="green")
            
            calendar_table.add_row("Total Days", str(analysis['total_days']))
            calendar_table.add_row("Trading Days", str(analysis['trading_days']))
            calendar_table.add_row("Non-Trading Days", str(analysis['non_trading_days']))
            calendar_table.add_row("Coverage Ratio", f"{analysis['coverage_ratio']:.1%}")
            
            if analysis.get('first_trading_day'):
                calendar_table.add_row("First Trading Day", str(analysis['first_trading_day']))
            if analysis.get('last_trading_day'):
                calendar_table.add_row("Last Trading Day", str(analysis['last_trading_day']))
                
            console.print(calendar_table)
            
            # Show trading efficiency
            if analysis['coverage_ratio'] >= 0.7:
                console.print("\n✅ [green]Good trading day coverage[/green]")
            elif analysis['coverage_ratio'] >= 0.5:
                console.print("\n⚠️  [yellow]Moderate trading day coverage[/yellow]")
            else:
                console.print("\n❌ [red]Low trading day coverage - consider extending range[/red]")
                
        else:
            console.print(f"❌ [red]Date range validation failed[/red]")
            console.print(f"💬 {result.message}")
            if result.suggestions:
                console.print(f"\n💡 Suggestions:")
                for suggestion in result.suggestions:
                    console.print(f"  • {suggestion}")
                    
    except Exception as e:
        console.print(f"❌ [red]Calendar analysis error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def monitor(
    live: bool = typer.Option(
        False,
        "--live", "-l",
        help="Show live status dashboard"
    ),
    operation_id: Optional[str] = typer.Option(
        None,
        "--operation", "-o",
        help="Monitor specific operation by ID"
    ),
    history: bool = typer.Option(
        False,
        "--history", "-h",
        help="Show operation history"
    ),
    cleanup: bool = typer.Option(
        False,
        "--cleanup",
        help="Clean up old completed operations"
    ),
    cleanup_days: int = typer.Option(
        7,
        "--cleanup-days",
        help="Days old for cleanup (default: 7)"
    )
):
    """
    Monitor ongoing operations and system status.
    
    This command provides real-time monitoring of active operations,
    background process tracking, and system resource usage.
    
    Examples:
        python main.py monitor --live           # Show live status dashboard
        python main.py monitor --history        # Show operation history
        python main.py monitor --operation ID   # Monitor specific operation
        python main.py monitor --cleanup        # Clean up old operations
    """
    
    if cleanup:
        console.print("🧹 [cyan]Cleaning up old operations...[/cyan]")
        monitor = OperationMonitor()
        monitor.cleanup_old_operations(cleanup_days)
        console.print(f"✅ [green]Cleanup completed (operations older than {cleanup_days} days)[/green]")
        return
    
    if live:
        console.print("🔄 [cyan]Starting live status dashboard...[/cyan]")
        console.print("💡 [dim]Press Ctrl+C to exit[/dim]\n")
        
        try:
            dashboard = LiveStatusDashboard()
            with dashboard.live_display() as dash:
                dash.update_status("Live monitoring active", "green")
                
                # Keep dashboard running
                import time
                while True:
                    time.sleep(1)
                    # Refresh operations every 5 seconds
                    if int(time.time()) % 5 == 0:
                        dash._refresh_operations()
                        dash._update_all_panels()
                        
        except KeyboardInterrupt:
            console.print("\n✅ [green]Dashboard stopped[/green]")
            
    elif history:
        monitor = OperationMonitor()
        history_ops = monitor.get_operation_history(limit=20)
        
        if not history_ops:
            console.print("📋 [dim]No operations found in history[/dim]")
            return
            
        # Create history table
        history_table = Table(show_header=True, header_style="bold cyan")
        history_table.add_column("Operation ID", style="yellow", width=25)
        history_table.add_column("Description", style="white", width=30)
        history_table.add_column("Status", width=12)
        history_table.add_column("Start Time", style="dim", width=20)
        history_table.add_column("Duration", width=10)
        
        for operation in history_ops:
            # Format status with color
            status = operation.get('status', 'unknown')
            status_color = {
                'completed': 'green',
                'failed': 'red',
                'cancelled': 'yellow',
                'running': 'cyan',
                'starting': 'blue'
            }.get(status, 'white')
            status_text = f"[{status_color}]{status}[/{status_color}]"
            
            # Format duration
            duration = "N/A"
            if 'duration_seconds' in operation:
                duration = format_duration(operation['duration_seconds'])
            elif operation.get('status') in ['running', 'starting', 'in_progress']:
                start_time = datetime.fromisoformat(operation['start_time'])
                elapsed = (datetime.now() - start_time).total_seconds()
                duration = f"~{format_duration(elapsed)}"
                
            # Format start time
            start_time = operation.get('start_time', '')
            if start_time:
                try:
                    start_dt = datetime.fromisoformat(start_time)
                    start_time = start_dt.strftime("%Y-%m-%d %H:%M")
                except:
                    start_time = start_time[:16]  # Truncate if parsing fails
                    
            history_table.add_row(
                operation.get('id', '')[:22] + "..." if len(operation.get('id', '')) > 25 else operation.get('id', ''),
                operation.get('config', {}).get('description', 'N/A')[:27] + "..." if len(operation.get('config', {}).get('description', '')) > 30 else operation.get('config', {}).get('description', 'N/A'),
                status_text,
                start_time,
                duration
            )
            
        console.print(f"\n📜 [bold cyan]Operation History (Last 20)[/bold cyan]\n")
        console.print(history_table)
        
    elif operation_id:
        monitor = OperationMonitor()
        if operation_id in monitor.operations:
            operation = monitor.operations[operation_id]
            
            # Show detailed operation info
            console.print(f"\n🔍 [bold cyan]Operation Details: {operation_id}[/bold cyan]\n")
            
            info_table = Table(show_header=False, box=None)
            info_table.add_column("Field", style="cyan", width=20)
            info_table.add_column("Value", style="white")
            
            info_table.add_row("ID", operation.get('id', 'N/A'))
            info_table.add_row("Status", operation.get('status', 'N/A'))
            info_table.add_row("Description", operation.get('config', {}).get('description', 'N/A'))
            info_table.add_row("Start Time", operation.get('start_time', 'N/A'))
            
            if 'end_time' in operation:
                info_table.add_row("End Time", operation['end_time'])
            if 'duration_seconds' in operation:
                info_table.add_row("Duration", format_duration(operation['duration_seconds']))
                
            info_table.add_row("Progress", f"{operation.get('progress', 0)}/{operation.get('total', 0)}")
            info_table.add_row("PID", str(operation.get('pid', 'N/A')))
            
            console.print(info_table)
            
            # Show metrics if available
            metrics = operation.get('metrics', {})
            if metrics:
                console.print(f"\n📊 [bold yellow]Metrics:[/bold yellow]")
                metrics_table = Table(show_header=False, box=None)
                metrics_table.add_column("Metric", style="cyan")
                metrics_table.add_column("Value", style="green")
                
                for key, value in metrics.items():
                    metrics_table.add_row(key.replace('_', ' ').title(), str(value))
                    
                console.print(metrics_table)
                
            # Show errors if any
            errors = operation.get('errors', [])
            if errors:
                console.print(f"\n❌ [bold red]Errors ({len(errors)}):[/bold red]")
                for i, error in enumerate(errors[-5:], 1):  # Show last 5 errors
                    console.print(f"  {i}. [red]{error}[/red]")
                    
        else:
            console.print(f"❌ [red]Operation '{operation_id}' not found[/red]")
            
    else:
        # Show quick status overview
        monitor = OperationMonitor()
        active_ops = monitor.get_active_operations()
        recent_ops = monitor.get_operation_history(limit=5)
        
        console.print("📊 [bold cyan]Operation Monitor - Quick Status[/bold cyan]\n")
        
        if active_ops:
            console.print(f"🔄 [green]{len(active_ops)} active operation(s)[/green]")
            for op in active_ops:
                description = op.get('config', {}).get('description', op.get('id', 'Unknown'))
                status = op.get('status', 'unknown')
                progress = op.get('progress', 0)
                total = op.get('total', 0)
                progress_text = f"{progress}/{total}" if total > 0 else "N/A"
                console.print(f"  • {description[:40]} - [{status}] {progress_text}")
        else:
            console.print("💤 [dim]No active operations[/dim]")
            
        if recent_ops:
            console.print(f"\n📜 Recent operations:")
            for op in recent_ops[:3]:
                description = op.get('config', {}).get('description', op.get('id', 'Unknown'))
                status = op.get('status', 'unknown')
                status_icon = {"completed": "✅", "failed": "❌", "cancelled": "⏹️"}.get(status, "❓")
                console.print(f"  {status_icon} {description[:40]}")
                
        console.print(f"\n💡 [dim]Use --live for real-time dashboard, --history for full history[/dim]")


@app.command("status-dashboard")
def status_dashboard(
    refresh_rate: float = typer.Option(
        2.0,
        "--refresh-rate", "-r",
        help="Dashboard refresh rate in Hz (default: 2.0)"
    ),
    show_system: bool = typer.Option(
        True,
        "--system/--no-system",
        help="Show system metrics panel"
    ),
    show_queue: bool = typer.Option(
        True,
        "--queue/--no-queue", 
        help="Show operation queue panel"
    )
):
    """
    Launch the live status dashboard with real-time monitoring.
    
    This provides a comprehensive real-time view of:
    - Active operations with progress bars
    - System resource usage (CPU, memory, network)
    - Operation queue and history
    - Background process monitoring
    
    Examples:
        python main.py status-dashboard              # Full dashboard
        python main.py status-dashboard --refresh-rate 1.0  # Faster refresh  
        python main.py status-dashboard --no-system   # Hide system metrics
    """
    console.print("🚀 [cyan]Launching Live Status Dashboard...[/cyan]")
    console.print("💡 [dim]Press Ctrl+C to exit dashboard[/dim]\n")
    
    try:
        dashboard = LiveStatusDashboard(
            title="📊 Historical Data Ingestor - Live Dashboard",
            show_system_metrics=show_system,
            show_operation_queue=show_queue,
            refresh_rate=refresh_rate
        )
        
        with dashboard.live_display() as dash:
            dash.update_status("Dashboard active - monitoring operations", "green")
            
            # Dashboard main loop
            import time
            last_refresh = 0
            
            while True:
                current_time = time.time()
                
                # Refresh operations data every 2 seconds
                if current_time - last_refresh >= 2:
                    dash._refresh_operations()
                    dash._update_all_panels()
                    last_refresh = current_time
                    
                time.sleep(0.1)  # Small sleep to prevent high CPU usage
                
    except KeyboardInterrupt:
        console.print("\n✅ [green]Dashboard stopped successfully[/green]")
    except Exception as e:
        console.print(f"\n❌ [red]Dashboard error: {e}[/red]")
        logger.error(f"Dashboard error: {e}")


@app.command()
def config(
    action: str = typer.Argument(
        ...,
        help="Action to perform: get, set, list, reset, export, import, validate, environment"
    ),
    key: Optional[str] = typer.Argument(
        None,
        help="Configuration key (for get/set actions). Use dot notation like 'progress.style'"
    ),
    value: Optional[str] = typer.Argument(
        None,
        help="Configuration value (for set action)"
    ),
    section: Optional[str] = typer.Option(
        None,
        "--section", "-s",
        help="Configuration section to focus on (progress, colors, display, behavior)"
    ),
    file_path: Optional[str] = typer.Option(
        None,
        "--file", "-f",
        help="File path for export/import operations"
    ),
    format: str = typer.Option(
        "yaml",
        "--format",
        help="Format for export/import (yaml or json)"
    ),
    save: bool = typer.Option(
        True,
        "--save/--no-save",
        help="Save changes to file (for set action)"
    ),
    apply_env: bool = typer.Option(
        False,
        "--apply-env",
        help="Apply environment optimizations"
    )
):
    """
    Manage CLI configuration settings.
    
    This command provides comprehensive configuration management for the CLI,
    including user preferences, environment detection, and optimization.
    
    Actions:
        get      - Get configuration value(s)
        set      - Set configuration value
        list     - List all configuration settings  
        reset    - Reset configuration to defaults
        export   - Export configuration to file
        import   - Import configuration from file
        validate - Validate current configuration
        environment - Show environment information
    
    Examples:
        # List all configuration
        python main.py config list
        
        # Get specific setting
        python main.py config get progress.style
        
        # Set configuration value
        python main.py config set progress.style advanced
        
        # List specific section
        python main.py config list --section progress
        
        # Reset configuration
        python main.py config reset
        python main.py config reset --section progress
        
        # Export/import configuration
        python main.py config export --file my-config.yaml
        python main.py config import --file my-config.yaml
        
        # Validate configuration
        python main.py config validate
        
        # Show environment info and apply optimizations
        python main.py config environment
        python main.py config set --apply-env
    """
    config_manager = get_config_manager()
    
    try:
        if action == "get":
            if not key:
                console.print("❌ [red]Key required for get action[/red]")
                console.print("💡 Use: python main.py config get <key>")
                raise typer.Exit(1)
                
            value = config_manager.get_setting(key)
            if value is not None:
                console.print(f"🔧 [cyan]{key}[/cyan] = [green]{value}[/green]")
            else:
                console.print(f"❌ [red]Setting '{key}' not found[/red]")
                
        elif action == "set":
            if apply_env:
                # Apply environment optimizations
                console.print("🔧 [cyan]Applying environment optimizations...[/cyan]")
                config_manager.apply_environment_optimizations(save)
                console.print("✅ [green]Environment optimizations applied[/green]")
            elif not key or value is None:
                console.print("❌ [red]Key and value required for set action[/red]")
                console.print("💡 Use: python main.py config set <key> <value>")
                raise typer.Exit(1)
            else:
                # Parse value based on type
                parsed_value = value
                if value.lower() in ['true', 'false']:
                    parsed_value = value.lower() == 'true'
                elif value.isdigit():
                    parsed_value = int(value)
                elif value.replace('.', '').isdigit():
                    try:
                        parsed_value = float(value)
                    except ValueError:
                        pass
                        
                config_manager.set_setting(key, parsed_value, save)
                console.print(f"✅ [green]Set {key} = {parsed_value}[/green]")
                
        elif action == "list":
            settings = config_manager.list_settings(section)
            
            if section:
                console.print(f"🔧 [bold cyan]Configuration - {section.title()} Section[/bold cyan]\n")
            else:
                console.print(f"🔧 [bold cyan]Complete Configuration[/bold cyan]\n")
                
            def _print_settings(data, prefix=""):
                for key, value in data.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, dict):
                        console.print(f"📁 [yellow]{full_key}[/yellow]:")
                        _print_settings(value, full_key)
                    else:
                        console.print(f"  🔧 [cyan]{full_key}[/cyan] = [green]{value}[/green]")
                        
            _print_settings(settings)
            
        elif action == "reset":
            if section:
                console.print(f"🔄 [yellow]Resetting {section} section to defaults...[/yellow]")
                config_manager.reset_config(section)
                console.print(f"✅ [green]{section.title()} section reset to defaults[/green]")
            else:
                console.print("🔄 [yellow]Resetting entire configuration to defaults...[/yellow]")
                config_manager.reset_config()
                console.print("✅ [green]Configuration reset to defaults[/green]")
                
        elif action == "export":
            if not file_path:
                # Generate default filename
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = f"hdi_config_{timestamp}.{format}"
                
            config_manager.export_config(Path(file_path), format)
            console.print(f"📤 [green]Configuration exported to {file_path}[/green]")
            
        elif action == "import":
            if not file_path:
                console.print("❌ [red]File path required for import action[/red]")
                console.print("💡 Use: python main.py config import --file <path>")
                raise typer.Exit(1)
                
            if not Path(file_path).exists():
                console.print(f"❌ [red]File not found: {file_path}[/red]")
                raise typer.Exit(1)
                
            config_manager.import_config(Path(file_path), merge=True, save=save)
            console.print(f"📥 [green]Configuration imported from {file_path}[/green]")
            
        elif action == "validate":
            errors = config_manager.validate_config()
            if errors:
                console.print("❌ [red]Configuration validation failed:[/red]\n")
                for error in errors:
                    console.print(f"  • [red]{error}[/red]")
                raise typer.Exit(1)
            else:
                console.print("✅ [green]Configuration is valid[/green]")
                
        elif action == "environment":
            env_info = config_manager.get_environment_info()
            
            console.print("🌍 [bold cyan]Environment Information[/bold cyan]\n")
            
            # Basic environment
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Platform", env_info['platform'])
            table.add_row("Terminal", f"{env_info['terminal_size']} ({'TTY' if env_info['is_tty'] else 'Non-TTY'})")
            table.add_row("Color Support", "Yes" if env_info['supports_color'] else "No")
            table.add_row("Unicode Support", "Yes" if env_info['supports_unicode'] else "No")
            table.add_row("CPU Cores", str(env_info['cpu_cores']))
            table.add_row("Recommended Workers", str(env_info['recommended_workers']))
            
            console.print(table)
            
            # Environment context
            console.print("\n🔍 [bold cyan]Environment Context[/bold cyan]")
            contexts = []
            if env_info['is_ci']:
                contexts.append("CI/CD Environment")
            if env_info['is_ssh']:
                contexts.append("SSH Session")
            if env_info['is_container']:
                contexts.append("Container Environment")
            if env_info['is_windows']:
                contexts.append("Windows Platform")
                
            if contexts:
                for context in contexts:
                    console.print(f"  🏷️  [yellow]{context}[/yellow]")
            else:
                console.print("  🖥️  [green]Local Interactive Environment[/green]")
                
            # Recommendations
            console.print("\n💡 [bold cyan]Recommended Settings[/bold cyan]")
            console.print(f"  📊 Progress Style: [green]{env_info['optimal_progress_style']}[/green]")
            console.print(f"  ⚡ Update Frequency: [green]{env_info['optimal_update_frequency']}[/green]")
            
            console.print("\n🔧 [dim]Use 'python main.py config set --apply-env' to apply these optimizations[/dim]")
            
        else:
            console.print(f"❌ [red]Unknown action: {action}[/red]")
            console.print("💡 Valid actions: get, set, list, reset, export, import, validate, environment")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"❌ [red]Configuration error: {e}[/red]")
        logger.error(f"Configuration error: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
