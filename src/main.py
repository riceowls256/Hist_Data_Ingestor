"""
Main entry point for the Historical Data Ingestor application.

This module provides the command-line interface for executing data ingestion
pipelines, querying stored data, and managing the system.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.pipeline_orchestrator import PipelineOrchestrator, PipelineError
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
