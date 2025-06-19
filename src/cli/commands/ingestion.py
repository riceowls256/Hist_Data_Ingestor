"""
Ingestion Commands Module

This module contains all data ingestion CLI commands including the main ingest
command and high-level backfill operations for batch processing.
"""

import csv
import json
import math
import os
import re
import sys
from datetime import datetime, date, timedelta
from decimal import Decimal
from io import StringIO
from pathlib import Path
from typing import Optional, List, Dict

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from dotenv import load_dotenv

from utils.custom_logger import get_logger
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
from cli.exchange_mapping import map_symbols_to_exchange
from cli.common.constants import SUPPORTED_SCHEMAS

# Initialize Rich console and logging
console = Console()
logger = get_logger(__name__)

# Create Typer app for ingestion commands
app = typer.Typer(
    name="ingestion",
    help="Data ingestion commands (ingest, backfill)",
    no_args_is_help=False
)


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
    """
    Execute data ingestion pipeline to fetch and store financial market data.
    
    This command fetches data from external APIs and stores it in TimescaleDB
    for later querying. It supports multiple data schemas and provides comprehensive
    validation and progress tracking.
    
    Examples:
        # Use predefined job configuration
        python main.py ingest --api databento --job ohlcv_daily_sample
        
        # Custom ingestion with specific parameters
        python main.py ingest --api databento --dataset GLBX.MDP3 --schema ohlcv-1d \\
            --symbols ES.FUT,CL.FUT --start-date 2024-01-01 --end-date 2024-01-31 \\
            --stype-in parent
        
        # Interactive guided mode
        python main.py ingest --guided
        
        # Preview operation without execution
        python main.py ingest --api databento --job test_job --dry-run
    """
    logger.info("command_started", command="ingest", api=api, job=job, dataset=dataset, 
                schema=schema, symbols=symbols, start_date=start_date, end_date=end_date, 
                stype_in=stype_in, force=force, dry_run=dry_run, guided=guided, user="cli")
    
    try:
        # Handle guided mode
        if guided:
            logger.info("guided_mode_started")
            console.print("🧭 [bold cyan]Guided Ingestion Mode[/bold cyan]")
            guided_params = GuidedMode.run_ingestion_wizard()
            if not guided_params:
                console.print("❌ [red]Guided mode cancelled by user[/red]")
                logger.info("guided_mode_cancelled")
                raise typer.Exit(code=1)
            
            # Update parameters with guided selections
            api = guided_params.get("api", api)
            job = guided_params.get("job", job)
            dataset = guided_params.get("dataset", dataset)
            schema = guided_params.get("schema", schema)
            symbols = guided_params.get("symbols", symbols)
            start_date = guided_params.get("start_date", start_date)
            end_date = guided_params.get("end_date", end_date)
            stype_in = guided_params.get("stype_in", stype_in)
            logger.info("guided_mode_completed", selected_params=guided_params.keys())
        
        # Create pipeline orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Load configuration
        config_manager = get_config_manager()
        
        # Handle job-based configuration
        if job:
            logger.info("job_loading_started", job=job, api=api)
            console.print(f"📋 [cyan]Loading predefined job: {job}[/cyan]")
            job_config = config_manager.get_job_config(api, job)
            if not job_config:
                console.print(f"❌ [red]Job '{job}' not found for API '{api}'[/red]")
                console.print(f"💡 [yellow]Use 'python main.py list-jobs --api {api}' to see available jobs[/yellow]")
                logger.error("job_loading_failed", job=job, api=api, reason="job_not_found")
                raise typer.Exit(code=1)
            
            # Override defaults with job config
            dataset = dataset or job_config.get("dataset")
            schema = schema or job_config.get("schema")
            symbols = symbols or job_config.get("symbols")
            start_date = start_date or job_config.get("start_date")
            end_date = end_date or job_config.get("end_date")
            stype_in = stype_in or job_config.get("stype_in")
            
        # Validate required parameters
        required_params = {
            "api": api,
            "dataset": dataset,
            "schema": schema,
            "symbols": symbols,
            "start_date": start_date,
            "end_date": end_date
        }
        
        missing_params = [param for param, value in required_params.items() if not value]
        if missing_params:
            console.print(f"❌ [red]Missing required parameters: {', '.join(missing_params)}[/red]")
            console.print("💡 [yellow]Use --guided mode for interactive parameter selection[/yellow]")
            console.print("💡 [yellow]Or specify parameters manually. Use --help for details.[/yellow]")
            logger.error("parameter_validation_failed", missing_params=missing_params)
            raise typer.Exit(code=1)
        
        # Parse symbols
        symbol_list = parse_symbols(symbols)
        
        # Validate parameters
        validation_errors = []
        
        # Date validation
        if not validate_date_format(start_date):
            validation_errors.append(f"Invalid start_date format: {start_date}. Use YYYY-MM-DD")
        
        if not validate_date_format(end_date):
            validation_errors.append(f"Invalid end_date format: {end_date}. Use YYYY-MM-DD")
        
        if start_date and end_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            if start_dt >= end_dt:
                validation_errors.append("Start date must be before end date")
            
            if start_dt == end_dt:
                validation_errors.append("Start date cannot equal end date. Use at least a 1-day range.")
        
        # Symbol validation with stype_in compatibility
        if stype_in and symbol_list:
            symbol_validation_errors = validate_symbol_stype_combination(symbol_list, stype_in)
            validation_errors.extend(symbol_validation_errors)
        
        # Schema validation - use comprehensive schema list with aliases
        valid_schemas = SUPPORTED_SCHEMAS + ["ohlcv"]  # Add "ohlcv" alias for backward compatibility
        if schema not in valid_schemas:
            validation_errors.append(f"Invalid schema: {schema}. Valid options: {', '.join(sorted(valid_schemas))}")
        
        if validation_errors:
            console.print("❌ [red]Validation errors:[/red]")
            for error in validation_errors:
                console.print(f"  • {error}")
            logger.error("input_validation_failed", validation_errors=validation_errors, error_count=len(validation_errors))
            raise typer.Exit(code=1)
        
        # Smart validation and suggestions
        try:
            smart_validator = create_smart_validator()
            validation_result = smart_validator.validate_ingestion_params(
                api=api,
                dataset=dataset,
                schema=schema,
                symbols=symbol_list,
                start_date=start_date,
                end_date=end_date,
                stype_in=stype_in
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
        
        # Market calendar pre-flight check
        try:
            from cli.smart_validation import MarketCalendarAnalyzer
            calendar_analyzer = MarketCalendarAnalyzer()
            
            market_analysis = calendar_analyzer.analyze_date_range(start_date, end_date)
            
            console.print(f"📅 [cyan]Market Calendar Analysis:[/cyan]")
            console.print(f"  • Total days: {market_analysis['total_days']}")
            console.print(f"  • Trading days: {market_analysis['trading_days']}")
            console.print(f"  • Weekend days: {market_analysis['weekend_days']}")
            console.print(f"  • Holidays: {market_analysis['holidays']}")
            
            if market_analysis['warnings']:
                console.print("⚠️  [yellow]Calendar warnings:[/yellow]")
                for warning in market_analysis['warnings']:
                    console.print(f"  • {warning}")
        
        except Exception as e:
            console.print(f"⚠️  [yellow]Market calendar analysis unavailable: {e}[/yellow]")
        
        # Create job configuration
        job_config = {
            "name": job or f"cli_{schema}_{symbols.replace(',', '_')}",
            "api": api,
            "dataset": dataset,
            "schema": schema,
            "symbols": symbol_list,
            "start_date": start_date,
            "end_date": end_date,
            "stype_in": stype_in,
            "created_at": datetime.now().isoformat(),
            "created_by": "cli_ingest"
        }
        
        # Display operation summary
        console.print(f"\n📊 [bold cyan]Ingestion Summary[/bold cyan]")
        console.print(f"API: {api}")
        console.print(f"Dataset: {dataset}")
        console.print(f"Schema: {schema}")
        console.print(f"Symbols: {', '.join(symbol_list)}")
        console.print(f"Date range: {start_date} to {end_date}")
        console.print(f"Symbol type: {stype_in or 'auto'}")
        console.print(f"Job name: {job_config['name']}")
        
        # Dry run mode
        if dry_run:
            console.print(f"\n🔍 [yellow]DRY RUN MODE - No data will be ingested[/yellow]")
            console.print("✅ [green]Configuration validation passed[/green]")
            console.print("✅ [green]All parameters are valid[/green]")
            console.print("🚀 [green]Ready to execute ingestion[/green]")
            console.print(f"💡 [blue]Remove --dry-run flag to execute ingestion[/blue]")
            logger.info("command_completed", command="ingest", mode="dry_run", job_name=job_config['name'], 
                       symbol_count=len(symbol_list), schema=schema)
            return
        
        # Confirmation prompt
        if not force:
            console.print(f"\n⚠️  [yellow]This will start data ingestion. Continue? [y/N][/yellow] ", end="")
            confirmation = input().strip().lower()
            if confirmation not in ['y', 'yes']:
                console.print("❌ [red]Ingestion cancelled by user[/red]")
                logger.info("command_cancelled", command="ingest", reason="user_declined")
                raise typer.Exit(code=1)
        
        # Execute ingestion
        console.print(f"\n🚀 [bold green]Starting ingestion...[/bold green]")
        logger.info("ingestion_execution_started", job_name=job_config['name'], symbol_count=len(symbol_list), 
                    schema=schema, date_range=f"{start_date}_to_{end_date}")
        
        with EnhancedProgress() as progress:
            # Create progress task
            task = progress.add_task(
                f"Ingesting {schema} data for {len(symbol_list)} symbols",
                total=None
            )
            
            # Execute pipeline
            result = orchestrator.execute_pipeline(job_config, progress_callback=progress.update)
            
            progress.update(task, completed=100, total=100)
        
        # Display results
        if result["status"] == "success":
            console.print(f"✅ [bold green]Ingestion completed successfully![/bold green]")
            console.print(f"📊 Records processed: {result.get('records_processed', 'N/A')}")
            console.print(f"⏱️  Duration: {format_duration(result.get('duration', 0))}")
            
            logger.info("command_completed", command="ingest", status="success", 
                       job_name=job_config['name'], records_processed=result.get('records_processed', 0),
                       duration_seconds=result.get('duration', 0), warning_count=len(result.get('warnings', [])))
            
            if result.get("warnings"):
                console.print(f"\n⚠️  [yellow]Warnings ({len(result['warnings'])}):[/yellow]")
                for warning in result["warnings"][:5]:  # Show first 5 warnings
                    console.print(f"  • {warning}")
                if len(result["warnings"]) > 5:
                    console.print(f"  ... and {len(result['warnings']) - 5} more warnings")
        
        else:
            console.print(f"❌ [bold red]Ingestion failed: {result.get('error', 'Unknown error')}[/bold red]")
            
            logger.error("command_failed", command="ingest", job_name=job_config['name'],
                        error=result.get('error', 'Unknown error'), 
                        troubleshooting_tips=result.get('troubleshooting_tips', []))
            
            if result.get("troubleshooting_tips"):
                console.print(f"\n💡 [blue]Troubleshooting tips:[/blue]")
                for tip in result["troubleshooting_tips"]:
                    console.print(f"  • {tip}")
            
            raise typer.Exit(code=1)
    
    except PipelineError as e:
        console.print(f"❌ [red]Pipeline error: {e}[/red]")
        console.print(f"💡 [blue]Use 'python main.py troubleshoot pipeline' for help[/blue]")
        logger.error("command_failed", command="ingest", error=str(e), error_type="PipelineError")
        raise typer.Exit(code=1)
    
    except Exception as e:
        console.print(f"❌ [red]Unexpected error: {e}[/red]")
        console.print(f"💡 [blue]Use 'python main.py troubleshoot' for general help[/blue]")
        logger.error("command_failed", command="ingest", error=str(e), error_type=type(e).__name__)
        raise typer.Exit(code=1)


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
    
    This command simplifies bulk data ingestion by using predefined symbol groups
    and lookback periods. It automatically calculates date ranges and handles
    batch processing for optimal performance.
    
    Examples:
        # Backfill 1 year of daily OHLCV data for S&P 500 sample
        python main.py backfill SP500_SAMPLE --lookback 1y
        
        # Backfill multiple schemas for energy futures
        python main.py backfill ENERGY_FUTURES --schemas ohlcv-1d,trades --lookback 6m
        
        # Custom symbol group with specific batch size
        python main.py backfill "ES.FUT,CL.FUT,NG.FUT" --batch-size 3 --lookback 3m
        
        # Preview operation without execution
        python main.py backfill SP500_SAMPLE --dry-run
    """
    logger.info("command_started", command="backfill", symbol_group=symbol_group, lookback=lookback, 
                schemas=schemas, api=api, dataset=dataset, batch_size=batch_size, 
                retry_failed=retry_failed, dry_run=dry_run, force=force, user="cli")
    
    try:
        # Initialize symbol group manager
        symbol_manager = SymbolGroupManager()
        
        # Resolve symbol group
        logger.info("symbol_group_resolution_started", symbol_group=symbol_group)
        console.print(f"🔍 [cyan]Resolving symbol group: {symbol_group}[/cyan]")
        
        if symbol_group in symbol_manager.get_predefined_groups():
            symbols = symbol_manager.get_group_symbols(symbol_group)
            console.print(f"📋 [green]Found predefined group with {len(symbols)} symbols[/green]")
            logger.info("symbol_group_resolved", group_type="predefined", symbol_count=len(symbols))
        else:
            # Treat as custom symbol list
            symbols = parse_symbols(symbol_group)
            console.print(f"📝 [green]Using custom symbol list with {len(symbols)} symbols[/green]")
            logger.info("symbol_group_resolved", group_type="custom", symbol_count=len(symbols))
        
        if not symbols:
            console.print(f"❌ [red]No symbols found for group: {symbol_group}[/red]")
            console.print(f"💡 [yellow]Use 'python main.py groups' to see available groups[/yellow]")
            logger.error("symbol_group_resolution_failed", symbol_group=symbol_group, reason="no_symbols_found")
            raise typer.Exit(code=1)
        
        # Calculate date range from lookback period
        end_date = date.today()
        
        # Parse lookback period
        lookback_mapping = {
            "1d": timedelta(days=1),
            "1w": timedelta(weeks=1),
            "1m": timedelta(days=30),
            "3m": timedelta(days=90),
            "6m": timedelta(days=180),
            "1y": timedelta(days=365),
            "3y": timedelta(days=365*3),
            "5y": timedelta(days=365*5),
            "10y": timedelta(days=365*10)
        }
        
        if lookback not in lookback_mapping:
            console.print(f"❌ [red]Invalid lookback period: {lookback}[/red]")
            console.print(f"💡 [yellow]Valid options: {', '.join(lookback_mapping.keys())}[/yellow]")
            logger.error("lookback_validation_failed", lookback=lookback, valid_options=list(lookback_mapping.keys()))
            raise typer.Exit(code=1)
        
        start_date = end_date - lookback_mapping[lookback]
        
        # Display operation summary
        console.print(f"\n📊 [bold cyan]Backfill Summary[/bold cyan]")
        console.print(f"Symbol group: {symbol_group}")
        console.print(f"Symbols: {', '.join(symbols[:10])}{' ...' if len(symbols) > 10 else ''} ({len(symbols)} total)")
        console.print(f"Lookback: {lookback} ({start_date} to {end_date})")
        console.print(f"Schemas: {', '.join(schemas)}")
        console.print(f"API: {api}")
        console.print(f"Dataset: {dataset}")
        console.print(f"Batch size: {batch_size}")
        
        # Estimate operation
        total_operations = len(symbols) * len(schemas)
        estimated_time = total_operations * 30  # Rough estimate: 30 seconds per operation
        
        console.print(f"\n📈 [cyan]Operation Estimate[/cyan]")
        console.print(f"Total operations: {total_operations}")
        console.print(f"Estimated time: {format_duration(estimated_time)}")
        console.print(f"Batch processing: {math.ceil(len(symbols) / batch_size)} batches")
        
        # Dry run mode
        if dry_run:
            console.print(f"\n🔍 [yellow]DRY RUN MODE - No data will be ingested[/yellow]")
            console.print("✅ [green]Operation plan validated[/green]")
            console.print("✅ [green]All parameters are valid[/green]")
            console.print("🚀 [green]Ready to execute backfill[/green]")
            console.print(f"💡 [blue]Remove --dry-run flag to execute backfill[/blue]")
            logger.info("command_completed", command="backfill", mode="dry_run", 
                       symbol_count=len(symbols), total_operations=total_operations, estimated_time=estimated_time)
            return
        
        # Confirmation prompt
        if not force:
            console.print(f"\n⚠️  [yellow]This will start backfill operation with {total_operations} ingestion jobs. Continue? [y/N][/yellow] ", end="")
            confirmation = input().strip().lower()
            if confirmation not in ['y', 'yes']:
                console.print("❌ [red]Backfill cancelled by user[/red]")
                logger.info("command_cancelled", command="backfill", reason="user_declined", 
                           total_operations=total_operations)
                raise typer.Exit(code=1)
        
        # Execute backfill
        console.print(f"\n🚀 [bold green]Starting backfill operation...[/bold green]")
        logger.info("backfill_execution_started", symbol_count=len(symbols), schema_count=len(schemas),
                    total_operations=total_operations, batch_size=batch_size)
        
        # Create pipeline orchestrator
        orchestrator = PipelineOrchestrator()
        
        # Track results
        results = {
            "successful": [],
            "failed": [],
            "warnings": []
        }
        
        with EnhancedProgress() as progress:
            # Create overall progress task
            overall_task = progress.add_task(
                f"Backfill progress",
                total=total_operations
            )
            
            completed_operations = 0
            
            # Process symbols in batches
            for batch_start in range(0, len(symbols), batch_size):
                batch_symbols = symbols[batch_start:batch_start + batch_size]
                
                console.print(f"\n📦 [cyan]Processing batch {batch_start//batch_size + 1}/{math.ceil(len(symbols)/batch_size)}[/cyan]")
                console.print(f"Symbols: {', '.join(batch_symbols)}")
                
                # Process each schema for this batch
                for schema in schemas:
                    for symbol in batch_symbols:
                        try:
                            # Create job config for this symbol/schema combination
                            job_config = {
                                "name": f"backfill_{schema}_{symbol}_{lookback}",
                                "api": api,
                                "dataset": dataset,
                                "schema": schema,
                                "symbols": [symbol],
                                "start_date": start_date.strftime("%Y-%m-%d"),
                                "end_date": end_date.strftime("%Y-%m-%d"),
                                "stype_in": "parent" if symbol.endswith(".FUT") else "continuous",
                                "created_at": datetime.now().isoformat(),
                                "created_by": "cli_backfill"
                            }
                            
                            # Execute pipeline for this symbol/schema
                            result = orchestrator.execute_pipeline(job_config)
                            
                            if result["status"] == "success":
                                results["successful"].append(f"{symbol} ({schema})")
                            else:
                                results["failed"].append(f"{symbol} ({schema}): {result.get('error', 'Unknown error')}")
                                
                                # Retry logic
                                if retry_failed:
                                    console.print(f"🔄 [yellow]Retrying {symbol} ({schema})...[/yellow]")
                                    retry_result = orchestrator.execute_pipeline(job_config)
                                    if retry_result["status"] == "success":
                                        results["successful"].append(f"{symbol} ({schema}) - retry")
                                        results["failed"].remove(f"{symbol} ({schema}): {result.get('error', 'Unknown error')}")
                            
                            if result.get("warnings"):
                                results["warnings"].extend(result["warnings"])
                            
                        except Exception as e:
                            error_msg = f"{symbol} ({schema}): {str(e)}"
                            results["failed"].append(error_msg)
                            console.print(f"❌ [red]Failed: {error_msg}[/red]")
                        
                        finally:
                            completed_operations += 1
                            progress.update(overall_task, completed=completed_operations)
        
        # Display final results
        console.print(f"\n📊 [bold cyan]Backfill Results[/bold cyan]")
        console.print(f"✅ Successful: {len(results['successful'])}")
        console.print(f"❌ Failed: {len(results['failed'])}")
        console.print(f"⚠️  Warnings: {len(results['warnings'])}")
        
        if results["successful"]:
            console.print(f"\n✅ [green]Successful operations:[/green]")
            for success in results["successful"][:10]:  # Show first 10
                console.print(f"  • {success}")
            if len(results["successful"]) > 10:
                console.print(f"  ... and {len(results['successful']) - 10} more")
        
        if results["failed"]:
            console.print(f"\n❌ [red]Failed operations:[/red]")
            for failure in results["failed"][:5]:  # Show first 5
                console.print(f"  • {failure}")
            if len(results["failed"]) > 5:
                console.print(f"  ... and {len(results['failed']) - 5} more")
        
        if results["warnings"]:
            console.print(f"\n⚠️  [yellow]Warnings (first 5):[/yellow]")
            for warning in results["warnings"][:5]:
                console.print(f"  • {warning}")
        
        # Log final results
        logger.info("command_completed", command="backfill", status="completed",
                    successful_operations=len(results["successful"]), 
                    failed_operations=len(results["failed"]),
                    warning_count=len(results["warnings"]),
                    total_operations=total_operations)
        
        # Exit with error if any operations failed
        if results["failed"]:
            console.print(f"\n💡 [blue]Use 'python main.py troubleshoot backfill' for help with failures[/blue]")
            logger.error("command_completed_with_failures", command="backfill", 
                        failed_operations=len(results["failed"]), 
                        successful_operations=len(results["successful"]))
            raise typer.Exit(code=1)
        
        console.print(f"\n🎉 [bold green]Backfill completed successfully![/bold green]")
    
    except Exception as e:
        console.print(f"❌ [red]Backfill operation failed: {e}[/red]")
        console.print(f"💡 [blue]Use 'python main.py troubleshoot backfill' for help[/blue]")
        logger.error("command_failed", command="backfill", error=str(e), error_type=type(e).__name__)
        raise typer.Exit(code=1)