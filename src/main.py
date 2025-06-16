"""
Main entry point for the Historical Data Ingestor application.

This module provides the command-line interface for executing data ingestion
pipelines, querying stored data, and managing the system.
"""

import csv
import json
import os
import sys
from datetime import datetime, date
from decimal import Decimal
from io import StringIO
from pathlib import Path
from typing import Optional, List, Dict, Any

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.pipeline_orchestrator import PipelineOrchestrator, PipelineError
from querying import QueryBuilder
from querying.exceptions import QueryingError, SymbolResolutionError, QueryExecutionError
from utils.custom_logger import setup_logging, get_logger

# Initialize the Typer app
app = typer.Typer(
    name="hist-data-ingestor",
    help="Historical Data Ingestor - Fetch and store financial market data",
    no_args_is_help=True
)

# Initialize Rich console for better output
console = Console()

# Set up logging
setup_logging()
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


def write_output_file(content: str, file_path: str, format_type: str):
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
        help="Limit number of results"
    ),
):
    """
    Query historical financial data from TimescaleDB.
    
    Examples:
    
        # Query daily OHLCV data for ES futures
        python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31
        
        # Query multiple symbols with CSV output
        python main.py query --symbols ES.c.0,NQ.c.0 --start-date 2024-01-01 --end-date 2024-01-31 --output-format csv
        
        # Query trades data with file output
        python main.py query -s ES.c.0 --schema trades --start-date 2024-01-01 --end-date 2024-01-01 --output-file trades.json --output-format json
        
        # Query with limit
        python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31 --limit 100
    """
    console.print("🔍 [bold blue]Querying historical financial data[/bold blue]")
    
    try:
        # Parse and validate symbols
        parsed_symbols = parse_query_symbols(symbols)
        if not parsed_symbols:
            console.print("❌ [red]Error: No valid symbols provided[/red]")
            raise typer.Exit(1)
        
        # Validate date format
        if not validate_date_format(start_date):
            console.print("❌ [red]Error: start-date must be in YYYY-MM-DD format[/red]")
            raise typer.Exit(1)
            
        if not validate_date_format(end_date):
            console.print("❌ [red]Error: end-date must be in YYYY-MM-DD format[/red]")
            raise typer.Exit(1)
        
        # Parse dates
        start_date_obj = parse_date_string(start_date)
        end_date_obj = parse_date_string(end_date)
        
        # Validate date range
        if start_date_obj > end_date_obj:
            console.print("❌ [red]Error: start-date must be before or equal to end-date[/red]")
            raise typer.Exit(1)
        
        # Validate schema
        if schema not in SCHEMA_MAPPING:
            console.print(f"❌ [red]Error: Invalid schema '{schema}'. Valid options: {', '.join(SCHEMA_MAPPING.keys())}[/red]")
            raise typer.Exit(1)
        
        # Validate output format
        if output_format not in ["table", "csv", "json"]:
            console.print("❌ [red]Error: Invalid output format. Valid options: table, csv, json[/red]")
            raise typer.Exit(1)
        
        # Validate query scope and get user confirmation if needed
        if not validate_query_scope(parsed_symbols, start_date_obj, end_date_obj, schema):
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
        
        console.print(config_table)
        
        # Execute query with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Querying {schema} data for {len(parsed_symbols)} symbols...", total=None)
            
            start_time = datetime.now()
            
            with QueryBuilder() as qb:
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
        console.print(f"\n📈 [bold green]Query completed successfully![/bold green]")
        console.print(f"Records: {len(results)} | Time: {execution_time:.2f}s | Schema: {schema}")
        
    except SymbolResolutionError as e:
        console.print(f"❌ [red]Symbol error: {e}[/red]")
        
        # Helpful suggestion - show available symbols
        try:
            with QueryBuilder() as qb:
                available = qb.get_available_symbols(limit=10)
                if available:
                    console.print("💡 [yellow]Available symbols (sample):[/yellow]")
                    for symbol in available[:5]:
                        console.print(f"   • {symbol}")
                    console.print("   Use 'python main.py query --help' for more information")
        except Exception:
            pass  # Don't fail if we can't get available symbols
        
        logger.error("Symbol resolution failed", error=str(e), symbols=parsed_symbols)
        raise typer.Exit(1)
        
    except QueryExecutionError as e:
        console.print(f"❌ [red]Database error: {e}[/red]")
        console.print("💡 [yellow]Check database connection and try again[/yellow]")
        logger.error("Query execution failed", error=str(e))
        raise typer.Exit(1)
        
    except QueryingError as e:
        console.print(f"❌ [red]Query error: {e}[/red]")
        logger.error("General querying error", error=str(e))
        raise typer.Exit(1)
        
    except Exception as e:
        console.print(f"❌ [red]Unexpected error: {e}[/red]")
        logger.error("Unexpected error in query command", error=str(e), error_type=type(e).__name__)
        raise typer.Exit(1)


@app.command()
def ingest(
    api: str = typer.Option(..., help="API type (currently supports: databento)"),
    job: Optional[str] = typer.Option(None, help="Predefined job name from config"),
    dataset: Optional[str] = typer.Option(None, help="Dataset identifier (e.g., GLBX.MDP3)"),
    schema: Optional[str] = typer.Option(None, help="Schema type (e.g., ohlcv-1d, trades, tbbo)"),
    symbols: Optional[str] = typer.Option(None, help="Comma-separated symbols (e.g., CL.FUT,ES.FUT)"),
    start_date: Optional[str] = typer.Option(None, help="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = typer.Option(None, help="End date (YYYY-MM-DD)"),
    stype_in: Optional[str] = typer.Option(None, help="Symbol type (continuous, native, parent)"),
    force: bool = typer.Option(False, "--force", help="Force execution without confirmation"),
):
    """
    Execute a data ingestion pipeline for the specified API and parameters.
    
    You can either use a predefined job name from the configuration file,
    or specify individual parameters to create a custom ingestion job.
    
    Examples:
    
        # Use a predefined job
        python main.py ingest --api databento --job ohlcv_1d
        
        # Custom job with specific parameters  
        python main.py ingest --api databento --dataset GLBX.MDP3 --schema ohlcv-1d \\
                       --symbols CL.FUT,ES.FUT --start-date 2023-01-01 --end-date 2023-12-31
    """
    console.print(f"🚀 [bold blue]Starting {api.upper()} data ingestion pipeline[/bold blue]")
    
    try:
        # Validate inputs
        if not job and not all([dataset, schema, symbols, start_date, end_date]):
            console.print("❌ [red]Error: Either specify --job or provide dataset, schema, symbols, start-date, and end-date[/red]")
            raise typer.Exit(1)
        
        if start_date and not validate_date_format(start_date):
            console.print("❌ [red]Error: start-date must be in YYYY-MM-DD format[/red]")
            raise typer.Exit(1)
            
        if end_date and not validate_date_format(end_date):
            console.print("❌ [red]Error: end-date must be in YYYY-MM-DD format[/red]")
            raise typer.Exit(1)
        
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
        else:
            console.print("📋 [cyan]Custom job configuration:[/cyan]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Parameter")
            table.add_column("Value")
            
            for key, value in overrides.items():
                table.add_row(key, str(value))
            
            console.print(table)
        
        if overrides:
            console.print(f"🔧 [yellow]Parameter overrides: {overrides}[/yellow]")
        
        # Confirmation prompt (unless forced)
        if not force:
            confirm = typer.confirm("Continue with this configuration?")
            if not confirm:
                console.print("⏹️  [yellow]Operation cancelled by user[/yellow]")
                raise typer.Exit(0)
        
        # Execute pipeline
        console.print("⚙️  [green]Initializing pipeline orchestrator...[/green]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Executing ingestion pipeline...", total=None)
            
            orchestrator = PipelineOrchestrator()
            success = orchestrator.execute_ingestion(
                api_type=api,
                job_name=job,
                overrides=overrides if overrides else None
            )
            
            progress.update(task, completed=True)
        
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
        logger.error("Pipeline execution failed", error=str(e))
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"❌ [red]Unexpected error: {e}[/red]")
        logger.error("Unexpected error in CLI", error=str(e), error_type=type(e).__name__)
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
        
        DB_USER = os.getenv('POSTGRES_USER')
        DB_PASSWORD = os.getenv('POSTGRES_PASSWORD') 
        DB_HOST = os.getenv('POSTGRES_HOST', 'timescaledb')
        DB_PORT = os.getenv('POSTGRES_PORT', '5432')
        DB_NAME = os.getenv('POSTGRES_DB')
        
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


if __name__ == "__main__":
    app()
