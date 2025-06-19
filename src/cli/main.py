"""
Main entry point for the Historical Data Ingestor CLI application.

This module provides the command-line interface for executing data ingestion
pipelines, querying stored data, and managing the system.
"""

import sys
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from dotenv import load_dotenv

# Load environment variables from .env file (override existing env vars)
load_dotenv(override=True)

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Initialize the main Typer app
app = typer.Typer(
    name="hist-data-ingestor",
    help="""📊 Historical Data Ingestor - Financial Market Data Pipeline
    
A production-ready system for ingesting, processing, and querying historical financial data.
Supports multiple data schemas (OHLCV, trades, quotes) with intelligent symbol resolution.
    
Quick Start:
  python main.py status              # Check system health
  python main.py version             # Show version information
  python main.py config list         # List configuration settings
    
For troubleshooting and more commands, see the full documentation.
    """,
    no_args_is_help=True,
    pretty_exceptions_show_locals=False
)

# Initialize Rich console for better output
console = Console()

# Set up logging with basic configuration for now
import logging
try:
    from utils.custom_logger import setup_logging, get_logger
    setup_logging(log_level="DEBUG", console_level="WARNING")
    logger = get_logger(__name__)
except ImportError:
    # Fallback if logging setup fails
    logging.basicConfig(level=logging.WARNING)
    logger = logging.getLogger(__name__)

# Import and register available command modules
success_count = 0
total_modules = 0

# System commands
try:
    from cli.commands.system import app as system_app
    success_count += 1
except ImportError as e:
    console.print(f"⚠️  [yellow]Could not load system commands: {e}[/yellow]")
total_modules += 1

# Help commands  
try:
    from cli.commands.help import app as help_app
    success_count += 1
except ImportError as e:
    console.print(f"⚠️  [yellow]Could not load help commands: {e}[/yellow]")
total_modules += 1

# Ingestion commands
try:
    from cli.commands.ingestion import app as ingestion_app
    success_count += 1
except ImportError as e:
    console.print(f"⚠️  [yellow]Could not load ingestion commands: {e}[/yellow]")
total_modules += 1

# Querying commands
try:
    from cli.commands.querying import app as querying_app
    success_count += 1
except ImportError as e:
    console.print(f"⚠️  [yellow]Could not load querying commands: {e}[/yellow]")
total_modules += 1

# Add system commands directly to main app for now
if 'system_app' in locals():
    @app.command()
    def status():
        """Check system status and connectivity."""
        from cli.commands.system import status as system_status
        return system_status()
    
    @app.command()
    def version():
        """Display version information."""
        from cli.commands.system import version as system_version
        return system_version()
    
    @app.command()
    def list_jobs(
        api: str = typer.Option("databento", help="API type to list jobs for")
    ):
        """List all available predefined jobs for the specified API."""
        from cli.commands.system import list_jobs as system_list_jobs
        return system_list_jobs(api)
    
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
        """Monitor ongoing operations and system status."""
        from cli.commands.system import monitor as system_monitor
        return system_monitor(live, operation_id, history, cleanup, cleanup_days)
    
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
        """Manage CLI configuration settings."""
        from cli.commands.system import config as system_config
        return system_config(action, key, value, section, file_path, format, save, apply_env)

    # Add help commands to main app if available
    if 'help_app' in locals():
        @app.command()
        def examples(
            command: Optional[str] = typer.Argument(
                None,
                help="Specific command to show examples for"
            )
        ):
            """Show practical examples for CLI commands."""
            from cli.commands.help import examples as help_examples
            return help_examples(command)
        
        @app.command()
        def troubleshoot(
            error: Optional[str] = typer.Argument(
                None,
                help="Error message or keyword to get specific help"
            )
        ):
            """Get troubleshooting help for common issues."""
            from cli.commands.help import troubleshoot as help_troubleshoot
            return help_troubleshoot(error)
        
        @app.command()
        def tips(
            category: Optional[str] = typer.Argument(
                None,
                help="Category of tips to show"
            )
        ):
            """Show usage tips and best practices."""
            from cli.commands.help import tips as help_tips
            return help_tips(category)
        
        @app.command()
        def schemas():
            """Display available data schemas and their fields."""
            from cli.commands.help import schemas as help_schemas
            return help_schemas()
        
        @app.command("help-menu")
        def help_menu():
            """Launch interactive help menu system."""
            from cli.commands.help import help_menu as help_help_menu
            return help_help_menu()
        
        @app.command()
        def quickstart():
            """Interactive setup wizard for new users."""
            from cli.commands.help import quickstart as help_quickstart
            return help_quickstart()
        
        @app.command()
        def cheatsheet():
            """Display quick reference cheat sheet."""
            from cli.commands.help import cheatsheet as help_cheatsheet
            return help_cheatsheet()

    # Add ingestion commands to main app if available
    if 'ingestion_app' in locals():
        @app.command()
        def ingest(
            api: str = typer.Option(..., help="API provider. Currently supports: databento"),
            job: Optional[str] = typer.Option(None, help="Predefined job name from config file. Use 'list-jobs' to see available jobs."),
            dataset: Optional[str] = typer.Option(None, help="Dataset identifier (e.g., GLBX.MDP3 for CME Globex)"),
            schema: Optional[str] = typer.Option(None, help="Data schema: ohlcv-1d (daily), ohlcv-1h (hourly), ohlcv-1m (minute), ohlcv-1s (second), trades, tbbo (quotes), statistics, definitions"),
            symbols: Optional[str] = typer.Option(None, help="Comma-separated symbols (e.g., ES.FUT,CL.FUT). See 'examples ingest' for formats."),
            start_date: Optional[str] = typer.Option(None, help="Start date in YYYY-MM-DD format"),
            end_date: Optional[str] = typer.Option(None, help="End date in YYYY-MM-DD format (inclusive)"),
            stype_in: Optional[str] = typer.Option(None, help="Symbol type: continuous (c.0), native, parent (.FUT)"),
            force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
            dry_run: bool = typer.Option(False, "--dry-run", help="Preview ingestion without execution"),
            guided: bool = typer.Option(False, "--guided", help="Use interactive guided mode to select parameters"),
        ):
            """Execute data ingestion pipeline to fetch and store financial market data."""
            from cli.commands.ingestion import ingest as ingestion_ingest
            return ingestion_ingest(api, job, dataset, schema, symbols, start_date, end_date, stype_in, force, dry_run, guided)
        
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
            """High-level backfill command for common use cases."""
            from cli.commands.ingestion import backfill as ingestion_backfill
            return ingestion_backfill(symbol_group, lookback, schemas, api, dataset, batch_size, retry_failed, dry_run, force)

    # Add querying commands to main app if available
    if 'querying_app' in locals():
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
            """Query historical financial data from TimescaleDB with intelligent symbol resolution."""
            from cli.commands.querying import query as querying_query
            return querying_query(symbols, start_date, end_date, schema, output_format, output_file, limit, dry_run, validate_only, guided)

# Report loading status
if success_count == total_modules:
    console.print(f"✅ [green]All {success_count}/{total_modules} command modules loaded successfully[/green]")
elif success_count > 0:
    console.print(f"⚠️  [yellow]{success_count}/{total_modules} command modules loaded[/yellow]")
else:
    console.print("❌ [red]No command modules could be loaded[/red]")
    console.print("📝 [dim]Commands will be unavailable until dependencies are resolved[/dim]")

# Placeholder commands for other modules (to be implemented)
@app.command()
def placeholder():
    """Placeholder for future commands."""
    console.print("🚧 [yellow]This command is not yet implemented in the refactored CLI[/yellow]")
    console.print("📝 [dim]Please use the original CLI or wait for migration completion[/dim]")

# Add help information
@app.command()
def info():
    """Show CLI refactoring information."""
    console.print("🔄 [bold cyan]CLI Refactoring Status[/bold cyan]\n")
    
    console.print("✅ [green]Completed:[/green]")
    console.print("  • System commands (status, version, config, monitor, list-jobs)")
    console.print("  • Help commands (examples, troubleshoot, tips, schemas, quickstart, help-menu, cheatsheet)")
    console.print("  • Ingestion commands (ingest, backfill)")
    console.print("  • Query commands (query)")
    console.print("  • CLI infrastructure and base classes")
    console.print("  • Shared utilities and constants")
    console.print("  • Comprehensive testing framework")
    
    console.print("\n🚧 [yellow]In Progress:[/yellow]")
    console.print("  • Integration testing")
    console.print("  • Performance optimization")
    
    console.print("\n⏳ [blue]Pending:[/blue]")
    console.print("  • Workflow commands (quickstart, workflows)")
    console.print("  • Validation commands (validate, market-calendar)")
    console.print("  • Symbol commands (groups, symbols, symbol-lookup)")
    
    console.print("\n📖 [dim]For complete functionality, use: python main.py (original CLI)[/dim]")


if __name__ == "__main__":
    app()