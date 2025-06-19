"""
Querying Commands Module

This module contains all data querying CLI commands including the main query
command with intelligent symbol resolution and multiple output formats.
"""

import csv
import json
import os
import sys
from datetime import datetime, date
from decimal import Decimal
from io import StringIO
from pathlib import Path
from typing import Optional, List, Dict, Tuple

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from dotenv import load_dotenv

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
from cli.config_manager import ConfigManager, get_config_manager, get_config
from cli.exchange_mapping import map_symbols_to_exchange
from cli.common.constants import SCHEMA_MAPPING, SUPPORTED_SCHEMAS

# Initialize Rich console and logging
console = Console()
logger = get_logger(__name__)

# Create Typer app for querying commands
app = typer.Typer(
    name="querying",
    help="Data querying commands (query, export)",
    no_args_is_help=False
)


def validate_date_format(date_str: str) -> bool:
    """Validate date string is in YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


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
    if not results:
        table = Table(title="Query Results")
        table.add_column("Message", style="yellow")
        table.add_row("No data found for the specified criteria")
        return table

    # Create table with schema-specific columns
    table = Table(title=f"Query Results ({schema.upper()})")
    
    # Get column names from first row
    if results:
        columns = list(results[0].keys())
        
        # Add columns with appropriate styling
        for col in columns:
            if col in ['symbol', 'instrument_id']:
                table.add_column(col, style="bold blue")
            elif col in ['ts_event', 'date', 'timestamp']:
                table.add_column(col, style="green")
            elif col in ['open_price', 'high_price', 'low_price', 'close_price', 'price']:
                table.add_column(col, style="cyan", justify="right")
            elif col in ['volume', 'trade_count', 'size']:
                table.add_column(col, style="magenta", justify="right")
            else:
                table.add_column(col)
        
        # Add rows (limit to first 100 for display)
        display_limit = min(len(results), 100)
        for i in range(display_limit):
            row = results[i]
            formatted_row = []
            for col in columns:
                value = row.get(col, '')
                
                # Format specific data types
                if isinstance(value, Decimal):
                    formatted_row.append(f"{value:.4f}")
                elif isinstance(value, (datetime, date)):
                    formatted_row.append(str(value))
                elif value is None:
                    formatted_row.append("")
                else:
                    formatted_row.append(str(value))
            
            table.add_row(*formatted_row)
        
        if len(results) > display_limit:
            table.add_row(*[f"... and {len(results) - display_limit} more rows" for _ in columns])
    
    return table


def format_csv_output(results: List[Dict]) -> str:
    """Format query results as CSV string."""
    if not results:
        return "# No data found for the specified criteria"
    
    output = StringIO()
    fieldnames = list(results[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    writer.writeheader()
    for row in results:
        # Convert Decimal and datetime objects to strings
        formatted_row = {}
        for key, value in row.items():
            if isinstance(value, Decimal):
                formatted_row[key] = str(value)
            elif isinstance(value, (datetime, date)):
                formatted_row[key] = str(value)
            elif value is None:
                formatted_row[key] = ""
            else:
                formatted_row[key] = value
        writer.writerow(formatted_row)
    
    return output.getvalue()


def format_json_output(results: List[Dict]) -> str:
    """Format query results as JSON string."""
    if not results:
        return json.dumps({"message": "No data found for the specified criteria", "results": []}, indent=2)
    
    # Convert Decimal and datetime objects for JSON serialization
    formatted_results = []
    for row in results:
        formatted_row = {}
        for key, value in row.items():
            if isinstance(value, Decimal):
                formatted_row[key] = float(value)
            elif isinstance(value, (datetime, date)):
                formatted_row[key] = value.isoformat()
            elif value is None:
                formatted_row[key] = None
            else:
                formatted_row[key] = value
        formatted_results.append(formatted_row)
    
    return json.dumps({
        "count": len(formatted_results),
        "results": formatted_results
    }, indent=2)


def write_output_file(content: str, file_path: str, format_type: str):
    """Write formatted content to file with proper error handling."""
    try:
        # Create directory if it doesn't exist
        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        console.print(f"✅ [green]Output written to: {file_path}[/green]")
        
        # Show file size
        file_size = output_path.stat().st_size
        if file_size > 1024 * 1024:  # > 1MB
            size_str = f"{file_size / (1024 * 1024):.2f} MB"
        elif file_size > 1024:  # > 1KB
            size_str = f"{file_size / 1024:.2f} KB"
        else:
            size_str = f"{file_size} bytes"
        
        console.print(f"📁 [dim]File size: {size_str}[/dim]")
        
    except Exception as e:
        console.print(f"❌ [red]Failed to write output file: {e}[/red]")
        raise typer.Exit(code=1)


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
        help="Schema type: ohlcv-1d (daily), ohlcv-1h (hourly), ohlcv-1m (minute), ohlcv-1s (second), trades, tbbo (quotes), statistics, definitions"
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
    
    This command retrieves stored data with comprehensive filtering and output options.
    Supports multiple data schemas and provides intelligent symbol resolution.
    
    Examples:
        # Basic daily OHLCV query
        python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31
        
        # Multiple symbols with CSV output
        python main.py query -s ES.c.0,NQ.c.0 --start-date 2024-01-01 --end-date 2024-01-31 \\
            --output-format csv --output-file results.csv
        
        # Trade data with limit
        python main.py query -s ES.c.0 --schema trades --start-date 2024-01-01 --end-date 2024-01-02 \\
            --limit 1000
        
        # Interactive guided mode
        python main.py query --guided
        
        # Validate parameters only
        python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31 --validate-only
    """
    log_user_message("Starting data query process")
    
    try:
        # Handle guided mode
        if guided:
            console.print("🧭 [bold cyan]Guided Query Mode[/bold cyan]")
            guided_params = GuidedMode.guided_query()
            if not guided_params:
                console.print("❌ [red]Guided mode cancelled by user[/red]")
                raise typer.Exit(code=1)
            
            # Update parameters with guided selections
            symbols = guided_params.get("symbols", symbols)
            start_date = guided_params.get("start_date", start_date)
            end_date = guided_params.get("end_date", end_date)
            schema = guided_params.get("schema", schema)
            output_format = guided_params.get("output_format", output_format)
            output_file = guided_params.get("output_file", output_file)
            limit = guided_params.get("limit", limit)
        
        # Parse and validate symbols
        parsed_symbols = parse_query_symbols(symbols)
        if not parsed_symbols:
            console.print("❌ [red]No valid symbols provided[/red]")
            console.print("💡 [yellow]Example: -s ES.c.0,NQ.c.0 or --symbols ES.c.0 --symbols NQ.c.0[/yellow]")
            raise typer.Exit(code=1)
        
        # Validate parameters
        validation_errors = []
        
        # Date validation
        if not validate_date_format(start_date):
            validation_errors.append(f"Invalid start_date format: {start_date}. Use YYYY-MM-DD")
        
        if not validate_date_format(end_date):
            validation_errors.append(f"Invalid end_date format: {end_date}. Use YYYY-MM-DD")
        
        if start_date and end_date:
            start_date_obj = parse_date_string(start_date)
            end_date_obj = parse_date_string(end_date)
            
            if start_date_obj >= end_date_obj:
                validation_errors.append("Start date must be before end date")
        
        # Schema validation
        valid_schemas = SUPPORTED_SCHEMAS + ["ohlcv"]  # Include alias
        if schema not in valid_schemas:
            validation_errors.append(f"Invalid schema: {schema}. Valid options: {', '.join(sorted(valid_schemas))}")
        
        # Output format validation
        valid_formats = ["table", "csv", "json"]
        if output_format not in valid_formats:
            validation_errors.append(f"Invalid output format: {output_format}. Valid options: {', '.join(valid_formats)}")
        
        # Limit validation
        if limit is not None and limit <= 0:
            validation_errors.append("Limit must be a positive integer")
        
        if validation_errors:
            console.print("❌ [red]Validation errors:[/red]")
            for error in validation_errors:
                console.print(f"  • {error}")
            raise typer.Exit(code=1)
        
        # Smart validation and suggestions
        try:
            smart_validator = create_smart_validator()
            validation_result = smart_validator.validate_query_params(
                symbols=parsed_symbols,
                start_date=start_date,
                end_date=end_date,
                schema=schema
            )
            
            if validation_result.warnings:
                console.print("⚠️  [yellow]Validation warnings:[/yellow]")
                for warning in validation_result.warnings:
                    console.print(f"  • {warning}")
            
            if validation_result.suggestions:
                console.print("💡 [blue]Suggestions:[/blue]")
                for suggestion in validation_result.suggestions:
                    console.print(f"  • {suggestion}")
        
        except Exception as e:
            console.print(f"⚠️  [yellow]Smart validation unavailable: {e}[/yellow]")
        
        # Parse dates for further processing
        start_date_obj = parse_date_string(start_date)
        end_date_obj = parse_date_string(end_date)
        
        # Query scope validation
        if not validate_query_scope(parsed_symbols, start_date_obj, end_date_obj, schema):
            console.print("❌ [red]Query cancelled by user[/red]")
            raise typer.Exit(code=1)
        
        # Display operation summary
        console.print(f"\n📊 [bold cyan]Query Summary[/bold cyan]")
        console.print(f"Symbols: {', '.join(parsed_symbols)}")
        console.print(f"Date range: {start_date} to {end_date}")
        console.print(f"Schema: {schema}")
        console.print(f"Output format: {output_format}")
        if output_file:
            console.print(f"Output file: {output_file}")
        if limit:
            console.print(f"Limit: {limit:,} records")
        
        # Validate-only mode
        if validate_only:
            console.print(f"\n✅ [green]Validation passed - parameters are valid[/green]")
            console.print(f"🔍 [blue]Query would retrieve {schema} data for {len(parsed_symbols)} symbols[/blue]")
            console.print(f"💡 [blue]Remove --validate-only flag to execute query[/blue]")
            return
        
        # Dry run mode
        if dry_run:
            console.print(f"\n🔍 [yellow]DRY RUN MODE - No query will be executed[/yellow]")
            console.print("✅ [green]Parameter validation passed[/green]")
            console.print("✅ [green]All parameters are valid[/green]")
            
            # Show what would be queried
            console.print(f"\n📋 [cyan]Query Preview:[/cyan]")
            console.print(f"  Schema method: {SCHEMA_MAPPING.get(schema, 'unknown')}")
            console.print(f"  Symbols: {parsed_symbols}")
            console.print(f"  Date range: {start_date_obj} to {end_date_obj}")
            console.print(f"  Expected columns: {_get_schema_columns(schema)}")
            
            console.print(f"\n🚀 [green]Ready to execute query[/green]")
            console.print(f"💡 [blue]Remove --dry-run flag to execute query[/blue]")
            return
        
        # Execute query
        console.print(f"\n🚀 [bold green]Executing query...[/bold green]")
        
        # Initialize QueryBuilder
        qb = QueryBuilder()
        
        # Get the appropriate query method
        if schema not in SCHEMA_MAPPING:
            console.print(f"❌ [red]Schema mapping not found for: {schema}[/red]")
            raise typer.Exit(code=1)
        
        query_method_name = SCHEMA_MAPPING[schema]
        if not hasattr(qb, query_method_name):
            console.print(f"❌ [red]Query method not implemented: {query_method_name}[/red]")
            raise typer.Exit(code=1)
        
        query_method = getattr(qb, query_method_name)
        
        # Build query parameters
        query_params = {
            "symbols": parsed_symbols,
            "start_date": start_date_obj,
            "end_date": end_date_obj
        }
        
        if limit:
            query_params["limit"] = limit
        
        # Execute query with progress tracking
        with EnhancedProgress() as progress:
            task = progress.add_task(
                f"Querying {schema} data for {len(parsed_symbols)} symbols",
                total=None
            )
            
            start_time = datetime.now()
            results = query_method(**query_params)
            end_time = datetime.now()
            
            progress.update(task, completed=100, total=100)
        
        # Calculate execution time
        execution_time = (end_time - start_time).total_seconds()
        
        # Display results summary
        console.print(f"\n📊 [bold green]Query completed successfully![/bold green]")
        console.print(f"📈 Records retrieved: {len(results):,}")
        console.print(f"⏱️  Execution time: {execution_time:.2f} seconds")
        
        if results:
            console.print(f"📅 Date range: {min(r.get('ts_event', r.get('date', 'N/A')) for r in results)} to {max(r.get('ts_event', r.get('date', 'N/A')) for r in results)}")
        
        # Format and display results
        if output_format == "table":
            table = format_table_output(results, schema)
            console.print(f"\n{table}")
            
            if len(results) > 100:
                console.print(f"\n💡 [blue]Showing first 100 of {len(results):,} results. Use --output-format csv/json for complete data.[/blue]")
        
        elif output_format == "csv":
            csv_content = format_csv_output(results)
            if output_file:
                write_output_file(csv_content, output_file, "csv")
            else:
                console.print(csv_content)
        
        elif output_format == "json":
            json_content = format_json_output(results)
            if output_file:
                write_output_file(json_content, output_file, "json")
            else:
                console.print(json_content)
        
        # Additional output file handling for table format
        if output_format == "table" and output_file:
            # For table format with output file, save as CSV
            csv_content = format_csv_output(results)
            write_output_file(csv_content, output_file, "csv")
        
        # Performance recommendations
        if execution_time > 10:
            console.print(f"\n💡 [yellow]Performance tip: Consider using --limit for large result sets[/yellow]")
        
        if len(results) > 10000:
            console.print(f"💡 [yellow]Large result set: Consider using date filters or --limit for better performance[/yellow]")
    
    except QueryingError as e:
        console.print(f"❌ [red]Query error: {e}[/red]")
        console.print(f"💡 [blue]Use 'python main.py troubleshoot query' for help[/blue]")
        raise typer.Exit(code=1)
    
    except SymbolResolutionError as e:
        console.print(f"❌ [red]Symbol resolution error: {e}[/red]")
        console.print(f"💡 [blue]Use 'python main.py symbol-lookup' to find valid symbols[/blue]")
        raise typer.Exit(code=1)
    
    except QueryExecutionError as e:
        console.print(f"❌ [red]Query execution error: {e}[/red]")
        console.print(f"💡 [blue]Check database connectivity and try again[/blue]")
        raise typer.Exit(code=1)
    
    except Exception as e:
        console.print(f"❌ [red]Unexpected error: {e}[/red]")
        console.print(f"💡 [blue]Use 'python main.py troubleshoot' for general help[/blue]")
        logger.exception("Query command failed with unexpected error")
        raise typer.Exit(code=1)


def _get_schema_columns(schema: str) -> str:
    """Get expected columns for schema (for dry run preview)."""
    schema_columns = {
        "ohlcv-1d": "symbol, date, open_price, high_price, low_price, close_price, volume, trade_count",
        "ohlcv-1h": "symbol, ts_event, open_price, high_price, low_price, close_price, volume, trade_count",
        "ohlcv-1m": "symbol, ts_event, open_price, high_price, low_price, close_price, volume, trade_count",
        "ohlcv-1s": "symbol, ts_event, open_price, high_price, low_price, close_price, volume, trade_count",
        "trades": "symbol, ts_event, price, size, side, trade_id",
        "tbbo": "symbol, ts_event, bid_px, ask_px, bid_sz, ask_sz",
        "statistics": "symbol, ts_event, stat_type, stat_value",
        "definitions": "symbol, instrument_id, raw_symbol, exchange, asset_type, expiration"
    }
    return schema_columns.get(schema, "varies by schema")