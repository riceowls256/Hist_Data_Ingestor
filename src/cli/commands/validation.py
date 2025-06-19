"""
Validation Commands Module

This module contains data validation CLI commands including smart validation
and comprehensive pandas market calendar integration for trading day analysis.
"""

import os
import sys
from datetime import datetime, date, timedelta
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
    import pandas as pd
    import pandas_market_calendars as mcal
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    console.print("⚠️  [yellow]pandas_market_calendars not available - some features may be limited[/yellow]")

try:
    from utils.custom_logger import setup_logging, get_logger, log_status, log_progress, log_user_message
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
    
    class MockSmartValidator:
        def validate_symbol(self, symbol): 
            return type('ValidationResult', (), {'is_valid': True, 'suggestions': []})()
        def validate_date_range(self, start, end, symbol=None, interactive=False):
            return type('ValidationResult', (), {'is_valid': True, 'metadata': {}, 'warnings': []})()
    
    def create_smart_validator():
        return MockSmartValidator()
    
    class MockEnhancedProgress:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def add_task(self, desc, total=None): return "mock_task"
        def add_subtask(self, desc, total=None): return "mock_task"
        def update(self, task, **kwargs): pass
    
    # Assign mocks to globals
    EnhancedProgress = MockEnhancedProgress
    SUPPORTED_SCHEMAS = ["ohlcv-1d", "ohlcv-1h", "trades", "tbbo", "statistics", "definitions"]

# Initialize logging
logger = get_logger(__name__)

# Create Typer app for validation commands
app = typer.Typer(
    name="validation",
    help="Data validation commands (validate, market-calendar)",
    no_args_is_help=False
)


def validate_date_format(date_str: str) -> bool:
    """Validate date string is in YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def get_available_exchanges() -> List[str]:
    """Get list of available market calendar exchanges."""
    if not PANDAS_AVAILABLE:
        return ["NYSE", "NASDAQ", "CME_Equity", "CME_Energy", "LSE"]
    
    try:
        # Get all available exchanges from pandas_market_calendars
        return sorted(mcal.get_calendar_names())
    except Exception:
        # Fallback to common exchanges
        return ["NYSE", "NASDAQ", "CME_Equity", "CME_Energy", "LSE", "TSX", "ASX"]


def analyze_market_calendar(start_date: str, end_date: str, exchange: str = "NYSE") -> Dict[str, Any]:
    """
    Analyze market calendar for given date range and exchange.
    
    Returns comprehensive calendar analysis including trading days, holidays,
    and market schedule information.
    """
    if not PANDAS_AVAILABLE:
        console.print("⚠️  [yellow]pandas_market_calendars not available - returning mock analysis[/yellow]")
        return _get_mock_calendar_analysis(start_date, end_date, exchange)
    
    try:
        # Get the market calendar
        calendar = mcal.get_calendar(exchange)
        
        # Parse dates
        start_dt = pd.Timestamp(start_date)
        end_dt = pd.Timestamp(end_date)
        
        # Get valid trading days
        trading_days = calendar.valid_days(start_date=start_dt, end_date=end_dt)
        
        # Get schedule with market open/close times
        schedule = calendar.schedule(start_date=start_dt, end_date=end_dt)
        
        # Calculate analytics
        total_days = (end_dt - start_dt).days + 1
        trading_days_count = len(trading_days)
        non_trading_days = total_days - trading_days_count
        
        # Get holidays in the range
        holidays = []
        try:
            # Try to get holiday information if available
            if hasattr(calendar, 'holidays'):
                holiday_dates = calendar.holidays().holidays
                for holiday_date in holiday_dates:
                    if start_dt <= pd.Timestamp(holiday_date) <= end_dt:
                        holidays.append(holiday_date.strftime('%Y-%m-%d'))
        except Exception:
            # Holidays not available for this calendar
            pass
        
        # Calculate coverage percentage
        coverage_pct = (trading_days_count / total_days) * 100 if total_days > 0 else 0
        
        return {
            "exchange": exchange,
            "start_date": start_date,
            "end_date": end_date,
            "total_days": total_days,
            "trading_days": trading_days_count,
            "non_trading_days": non_trading_days,
            "coverage_percentage": coverage_pct,
            "holidays": holidays,
            "trading_days_list": [dt.strftime('%Y-%m-%d') for dt in trading_days],
            "schedule": schedule,
            "analysis_success": True
        }
        
    except Exception as e:
        logger.exception(f"Market calendar analysis failed: {e}")
        console.print(f"⚠️  [yellow]Calendar analysis failed, using fallback: {e}[/yellow]")
        return _get_mock_calendar_analysis(start_date, end_date, exchange)


def _get_mock_calendar_analysis(start_date: str, end_date: str, exchange: str) -> Dict[str, Any]:
    """Provide mock calendar analysis when pandas_market_calendars is not available."""
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        total_days = (end_dt - start_dt).days + 1
        
        # Rough estimation: ~70% trading days (excluding weekends and holidays)
        estimated_trading_days = int(total_days * 0.7)
        non_trading_days = total_days - estimated_trading_days
        coverage_pct = (estimated_trading_days / total_days) * 100
        
        return {
            "exchange": exchange,
            "start_date": start_date,
            "end_date": end_date,
            "total_days": total_days,
            "trading_days": estimated_trading_days,
            "non_trading_days": non_trading_days,
            "coverage_percentage": coverage_pct,
            "holidays": [],
            "trading_days_list": [],
            "schedule": None,
            "analysis_success": False,
            "note": "Mock analysis - install pandas_market_calendars for accurate results"
        }
    except Exception:
        return {
            "exchange": exchange,
            "start_date": start_date,
            "end_date": end_date,
            "analysis_success": False,
            "error": "Date parsing failed"
        }


@app.command()
def validate(
    input_value: str = typer.Argument(..., help="Value to validate"),
    input_type: str = typer.Option(
        "symbol",
        "--type", "-t",
        help="Type of validation: symbol, symbol_list, schema, date, date_range"
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
        python main.py validate 2024-01-01 --type date             # Validate date format
        python main.py validate "" --type date_range --start-date 2024-01-01 --end-date 2024-12-31
    """
    log_user_message(f"Validating {input_type}: {input_value}")
    console.print(f"\n🔍 [bold cyan]Validating {input_type}: {input_value}[/bold cyan]\n")
    
    try:
        # Initialize validation results
        validation_passed = True
        warnings = []
        suggestions = []
        
        if input_type == "date_range":
            if not start_date or not end_date:
                console.print("❌ [red]Date range validation requires --start-date and --end-date[/red]")
                raise typer.Exit(code=1)
            
            # Validate date formats
            if not validate_date_format(start_date):
                console.print(f"❌ [red]Invalid start_date format: {start_date}[/red]")
                validation_passed = False
            
            if not validate_date_format(end_date):
                console.print(f"❌ [red]Invalid end_date format: {end_date}[/red]")
                validation_passed = False
            
            if validation_passed:
                # Use smart validator for date range analysis
                try:
                    validator = create_smart_validator()
                    result = validator.validate_date_range(start_date, end_date, interactive=interactive)
                    
                    if result.is_valid:
                        console.print("✅ [green]Date range is valid[/green]")
                        if hasattr(result, 'warnings') and result.warnings:
                            warnings.extend(result.warnings)
                    else:
                        console.print("❌ [red]Date range validation failed[/red]")
                        validation_passed = False
                        
                except Exception as e:
                    console.print(f"⚠️  [yellow]Smart validation unavailable: {e}[/yellow]")
                    console.print("✅ [green]Basic date format validation passed[/green]")
        
        elif input_type == "date":
            if validate_date_format(input_value):
                console.print("✅ [green]Date format is valid[/green]")
            else:
                console.print(f"❌ [red]Invalid date format: {input_value}[/red]")
                console.print("💡 [blue]Expected format: YYYY-MM-DD (e.g., 2024-01-01)[/blue]")
                validation_passed = False
        
        elif input_type == "schema":
            if input_value in SUPPORTED_SCHEMAS:
                console.print(f"✅ [green]Schema '{input_value}' is valid[/green]")
            else:
                console.print(f"❌ [red]Invalid schema: {input_value}[/red]")
                console.print(f"💡 [blue]Valid schemas: {', '.join(SUPPORTED_SCHEMAS)}[/blue]")
                validation_passed = False
        
        elif input_type == "symbol":
            try:
                validator = create_smart_validator()
                result = validator.validate_symbol(input_value)
                
                if result.is_valid:
                    console.print(f"✅ [green]Symbol '{input_value}' is valid[/green]")
                else:
                    console.print(f"❌ [red]Symbol '{input_value}' validation failed[/red]")
                    validation_passed = False
                
                if hasattr(result, 'suggestions') and result.suggestions:
                    suggestions.extend(result.suggestions)
                    
            except Exception as e:
                console.print(f"⚠️  [yellow]Smart symbol validation unavailable: {e}[/yellow]")
                # Basic symbol format validation
                if input_value and len(input_value) > 0:
                    console.print(f"✅ [green]Symbol '{input_value}' has valid format[/green]")
                else:
                    console.print("❌ [red]Empty symbol provided[/red]")
                    validation_passed = False
        
        elif input_type == "symbol_list":
            symbols = [s.strip() for s in input_value.split(",") if s.strip()]
            if not symbols:
                console.print("❌ [red]No valid symbols found in list[/red]")
                validation_passed = False
            else:
                console.print(f"✅ [green]Found {len(symbols)} symbols in list[/green]")
                for symbol in symbols:
                    console.print(f"  • {symbol}")
        
        else:
            console.print(f"❌ [red]Unknown validation type: {input_type}[/red]")
            console.print("💡 [blue]Valid types: symbol, symbol_list, schema, date, date_range[/blue]")
            validation_passed = False
        
        # Display warnings if any
        if warnings:
            console.print("\n⚠️  [yellow]Warnings:[/yellow]")
            for warning in warnings:
                console.print(f"  • {warning}")
        
        # Display suggestions if any
        if suggestions:
            console.print("\n💡 [blue]Suggestions:[/blue]")
            for suggestion in suggestions:
                console.print(f"  • {suggestion}")
        
        # Final result
        if validation_passed:
            console.print(f"\n✅ [bold green]Validation passed for {input_type}[/bold green]")
        else:
            console.print(f"\n❌ [bold red]Validation failed for {input_type}[/bold red]")
            raise typer.Exit(code=1)
    
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"❌ [red]Validation error: {e}[/red]")
        console.print(f"💡 [blue]Use 'python main.py troubleshoot validate' for help[/blue]")
        logger.exception("Validation command failed")
        raise typer.Exit(code=1)


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
    📅 Market calendar analysis and trading day validation.
    
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
    log_user_message(f"Market calendar analysis: {start_date} to {end_date}, exchange: {exchange}")
    
    try:
        # Handle list exchanges option
        if list_exchanges:
            console.print("\n📅 [bold cyan]Available Market Calendar Exchanges[/bold cyan]\n")
            exchanges = get_available_exchanges()
            
            # Display exchanges in a nice table
            table = Table(title="Market Calendar Exchanges")
            table.add_column("Exchange", style="bold blue")
            table.add_column("Description", style="cyan")
            
            exchange_descriptions = {
                "NYSE": "New York Stock Exchange",
                "NASDAQ": "NASDAQ Stock Market",
                "CME_Equity": "CME Group Equity Futures",
                "CME_Energy": "CME Group Energy Futures",
                "LSE": "London Stock Exchange",
                "TSX": "Toronto Stock Exchange",
                "ASX": "Australian Securities Exchange",
                "EUREX": "European Exchange",
                "HKEX": "Hong Kong Exchange"
            }
            
            for exch in exchanges:
                description = exchange_descriptions.get(exch, "Market exchange")
                table.add_row(exch, description)
            
            console.print(table)
            console.print(f"\n💡 [blue]Use --exchange EXCHANGE_NAME to analyze specific exchange[/blue]")
            return
        
        # Validate date formats
        if not validate_date_format(start_date):
            console.print(f"❌ [red]Invalid start_date format: {start_date}[/red]")
            console.print("💡 [blue]Expected format: YYYY-MM-DD[/blue]")
            raise typer.Exit(code=1)
        
        if not validate_date_format(end_date):
            console.print(f"❌ [red]Invalid end_date format: {end_date}[/red]")
            console.print("💡 [blue]Expected format: YYYY-MM-DD[/blue]")
            raise typer.Exit(code=1)
        
        # Validate date order
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        if start_dt >= end_dt:
            console.print("❌ [red]Start date must be before end date[/red]")
            raise typer.Exit(code=1)
        
        console.print(f"\n📅 [bold cyan]Market Calendar Analysis[/bold cyan]\n")
        console.print(f"📊 Date Range: {start_date} to {end_date}")
        console.print(f"🏢 Exchange: {exchange}")
        
        # Perform calendar analysis
        console.print("🔄 [cyan]Analyzing market calendar...[/cyan]")
        analysis = analyze_market_calendar(start_date, end_date, exchange)
        
        if not analysis.get("analysis_success", False):
            console.print(f"⚠️  [yellow]Calendar analysis completed with limitations[/yellow]")
            if "note" in analysis:
                console.print(f"📝 [dim]{analysis['note']}[/dim]")
        
        # Display results based on options
        if coverage_only:
            # Show only coverage summary
            console.print(f"\n📈 [bold green]Coverage Summary[/bold green]")
            console.print(f"Total Days: {analysis['total_days']}")
            console.print(f"Trading Days: {analysis['trading_days']}")
            console.print(f"Coverage: {analysis['coverage_percentage']:.1f}%")
        else:
            # Show detailed analysis
            console.print(f"\n📊 [bold green]Calendar Analysis Results[/bold green]")
            
            # Create results table
            table = Table(title=f"{exchange} Market Calendar Analysis")
            table.add_column("Metric", style="bold blue")
            table.add_column("Value", style="green", justify="right")
            
            table.add_row("Total Days", str(analysis['total_days']))
            table.add_row("Trading Days", str(analysis['trading_days']))
            table.add_row("Non-Trading Days", str(analysis['non_trading_days']))
            table.add_row("Coverage Percentage", f"{analysis['coverage_percentage']:.1f}%")
            
            if analysis.get('holidays'):
                table.add_row("Holidays Found", str(len(analysis['holidays'])))
            
            console.print(table)
            
            # Show holidays if requested
            if show_holidays and analysis.get('holidays'):
                console.print(f"\n🏖️  [bold cyan]Holidays in Date Range[/bold cyan]")
                for holiday in analysis['holidays']:
                    console.print(f"  • {holiday}")
            
            # Show schedule if requested
            if show_schedule and analysis.get('schedule') is not None:
                console.print(f"\n🕐 [bold cyan]Market Schedule[/bold cyan]")
                try:
                    if PANDAS_AVAILABLE and not analysis['schedule'].empty:
                        # Display first few schedule entries
                        schedule_sample = analysis['schedule'].head(10)
                        console.print(f"📅 Showing first {len(schedule_sample)} trading days:")
                        for idx, row in schedule_sample.iterrows():
                            date_str = idx.strftime('%Y-%m-%d')
                            market_open = row.get('market_open', 'N/A')
                            market_close = row.get('market_close', 'N/A')
                            console.print(f"  • {date_str}: {market_open} - {market_close}")
                        
                        if len(analysis['schedule']) > 10:
                            console.print(f"  ... and {len(analysis['schedule']) - 10} more trading days")
                    else:
                        console.print("📝 [dim]Schedule details not available[/dim]")
                except Exception as e:
                    console.print(f"⚠️  [yellow]Schedule display error: {e}[/yellow]")
        
        # Performance recommendations
        days_span = analysis['total_days']
        if days_span > 365:
            console.print(f"\n💡 [yellow]Large date range ({days_span} days) - consider smaller ranges for better API performance[/yellow]")
        
        # Trading day recommendations
        trading_days = analysis['trading_days']
        if trading_days > 100:
            console.print(f"💡 [blue]High-frequency data over {trading_days} trading days may be substantial[/blue]")
        
        console.print(f"\n✅ [bold green]Market calendar analysis completed successfully![/bold green]")
    
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"❌ [red]Market calendar analysis failed: {e}[/red]")
        console.print(f"💡 [blue]Use 'python main.py troubleshoot market-calendar' for help[/blue]")
        logger.exception("Market calendar command failed")
        raise typer.Exit(code=1)


# Export the app for module imports
__all__ = ["app", "validate", "market_calendar", "analyze_market_calendar", "get_available_exchanges"]