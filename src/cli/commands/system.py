"""
System Commands Module

This module contains all system-related CLI commands including status checks,
version information, configuration management, monitoring, and job listing.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from core.pipeline_orchestrator import PipelineOrchestrator
from cli.progress_utils import OperationMonitor, LiveStatusDashboard, format_duration
from cli.config_manager import get_config_manager
from utils.custom_logger import get_logger

# Initialize Rich console and logging
console = Console()
logger = get_logger(__name__)

# Create Typer app for system commands
app = typer.Typer(
    name="system",
    help="System management commands (status, version, config, monitor)",
    no_args_is_help=False
)


@app.command()
def list_jobs(
    api: str = typer.Option("databento", help="API type to list jobs for")
):
    """List all available predefined jobs for the specified API."""
    logger.info("command_started", command="list_jobs", api=api, user="cli")
    console.print(f"📋 [bold blue]Available jobs for {api.upper()}:[/bold blue]")

    try:
        orchestrator = PipelineOrchestrator()
        api_config = orchestrator.load_api_config(api)
        jobs = api_config.get("jobs", [])

        if not jobs:
            console.print("ℹ️  [yellow]No predefined jobs found[/yellow]")
            logger.info("command_completed", command="list_jobs", api=api, job_count=0, status="no_jobs")
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
        logger.info("command_completed", command="list_jobs", api=api, job_count=len(jobs), status="success")

    except Exception as e:
        console.print(f"❌ [red]Failed to load jobs: {e}[/red]")
        logger.error("command_failed", command="list_jobs", api=api, error=str(e), error_type=type(e).__name__)
        raise typer.Exit(1)


@app.command()
def status():
    """Check system status and connectivity."""
    logger.info("command_started", command="status", user="cli")
    console.print("🔍 [bold blue]Checking system status...[/bold blue]")

    status_results = {
        "database_connected": False,
        "api_key_configured": False,
        "log_directory_exists": False
    }

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
            logger.error("system_check_failed", component="database", reason="missing_env_vars")
            raise typer.Exit(1)

        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        console.print("✅ [green]TimescaleDB connection: OK[/green]")
        status_results["database_connected"] = True
        logger.info("system_check_success", component="database", host=DB_HOST, port=DB_PORT, dbname=DB_NAME)
        conn.close()

    except Exception as e:
        console.print(f"❌ [red]TimescaleDB connection: FAILED ({e})[/red]")
        logger.error("system_check_failed", component="database", error=str(e), error_type=type(e).__name__)

    # Check API key availability
    databento_key = os.getenv('DATABENTO_API_KEY')
    if databento_key:
        console.print("✅ [green]Databento API key: Configured[/green]")
        status_results["api_key_configured"] = True
        logger.info("system_check_success", component="api_key", provider="databento")
    else:
        console.print("❌ [red]Databento API key: Not configured[/red]")
        logger.warning("system_check_warning", component="api_key", provider="databento", reason="not_configured")

    # Check log directory
    log_dir = Path("logs")
    if log_dir.exists():
        console.print("✅ [green]Log directory: OK[/green]")
        status_results["log_directory_exists"] = True
        logger.info("system_check_success", component="log_directory", path=str(log_dir))
    else:
        console.print("⚠️  [yellow]Log directory: Missing (will be created)[/yellow]")
        logger.warning("system_check_warning", component="log_directory", path=str(log_dir), reason="missing")

    console.print("\n📊 [bold cyan]System Information:[/bold cyan]")
    info_table = Table(show_header=True, header_style="bold magenta")
    info_table.add_column("Component")
    info_table.add_column("Status")

    info_table.add_row("Python Version", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    info_table.add_row("Working Directory", str(Path.cwd()))
    info_table.add_row("Config Directory", str(Path("configs")))

    console.print(info_table)
    
    # Log overall status
    overall_status = "healthy" if all(status_results.values()) else "degraded"
    logger.info("command_completed", command="status", status=overall_status, **status_results)


@app.command()
def version():
    """Display version information."""
    logger.info("command_started", command="version", user="cli")
    
    version_info = {
        "app_version": "1.0.0-mvp",
        "build": "Story 2.6 Implementation",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "cli_framework": "Typer with Rich formatting"
    }
    
    console.print("🏷️  [bold blue]Historical Data Ingestor[/bold blue]")
    console.print(f"Version: {version_info['app_version']}")
    console.print(f"Build: {version_info['build']}")
    console.print(f"Python: {version_info['python_version']}")
    console.print(f"CLI Framework: {version_info['cli_framework']}")
    
    logger.info("command_completed", command="version", **version_info)


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
    
    logger.info("command_started", command="monitor", live=live, operation_id=operation_id, 
                history=history, cleanup=cleanup, cleanup_days=cleanup_days, user="cli")
    
    if cleanup:
        console.print("🧹 [cyan]Cleaning up old operations...[/cyan]")
        logger.info("monitor_cleanup_started", cleanup_days=cleanup_days)
        monitor_instance = OperationMonitor()
        monitor_instance.cleanup_old_operations(cleanup_days)
        console.print(f"✅ [green]Cleanup completed (operations older than {cleanup_days} days)[/green]")
        logger.info("monitor_cleanup_completed", cleanup_days=cleanup_days)
        return
    
    if live:
        console.print("🔄 [cyan]Starting live status dashboard...[/cyan]")
        console.print("💡 [dim]Press Ctrl+C to exit[/dim]\n")
        logger.info("monitor_live_dashboard_started")
        
        try:
            dashboard = LiveStatusDashboard()
            with dashboard.live_display() as dash:
                dash.update_status("Live monitoring active", "green")
                
                # Keep dashboard running
                import time
                start_time = time.time()
                while True:
                    time.sleep(1)
                    # Refresh operations every 5 seconds
                    if int(time.time()) % 5 == 0:
                        dash._refresh_operations()
                        dash._update_all_panels()
                        
        except KeyboardInterrupt:
            console.print("\n✅ [green]Dashboard stopped[/green]")
            runtime = time.time() - start_time
            logger.info("monitor_live_dashboard_stopped", runtime_seconds=runtime, stop_reason="user_interrupt")
            
    elif history:
        logger.info("monitor_history_requested", limit=20)
        monitor_instance = OperationMonitor()
        history_ops = monitor_instance.get_operation_history(limit=20)
        
        if not history_ops:
            console.print("📋 [dim]No operations found in history[/dim]")
            logger.info("monitor_history_completed", operation_count=0)
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
        logger.info("monitor_history_completed", operation_count=len(history_ops))
        
    elif operation_id:
        logger.info("monitor_operation_requested", operation_id=operation_id)
        monitor_instance = OperationMonitor()
        if operation_id in monitor_instance.operations:
            operation = monitor_instance.operations[operation_id]
            
            # Show detailed operation info
            console.print(f"\n🔍 [bold cyan]Operation Details: {operation_id}[/bold cyan]\n")
            logger.info("monitor_operation_found", operation_id=operation_id, status=operation.get('status', 'unknown'))
            
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
            logger.warning("monitor_operation_not_found", operation_id=operation_id)
            
    else:
        # Show quick status overview
        logger.info("monitor_overview_requested")
        monitor_instance = OperationMonitor()
        active_ops = monitor_instance.get_active_operations()
        recent_ops = monitor_instance.get_operation_history(limit=5)
        
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
        logger.info("monitor_overview_completed", active_operations=len(active_ops), recent_operations=len(recent_ops))


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
    logger.info("command_started", command="config", action=action, key=key, value=value, 
                section=section, file_path=file_path, format=format, save=save, apply_env=apply_env, user="cli")
    config_manager = get_config_manager()
    
    try:
        if action == "get":
            if not key:
                console.print("❌ [red]Key required for get action[/red]")
                console.print("💡 Use: python main.py config get <key>")
                logger.error("config_action_failed", action="get", reason="missing_key")
                raise typer.Exit(1)
                
            value = config_manager.get_setting(key)
            if value is not None:
                console.print(f"🔧 [cyan]{key}[/cyan] = [green]{value}[/green]")
                logger.info("config_action_completed", action="get", key=key, value=str(value))
            else:
                console.print(f"❌ [red]Setting '{key}' not found[/red]")
                logger.warning("config_action_failed", action="get", key=key, reason="key_not_found")
                
        elif action == "set":
            if apply_env:
                # Apply environment optimizations
                console.print("🔧 [cyan]Applying environment optimizations...[/cyan]")
                logger.info("config_applying_env_optimizations")
                config_manager.apply_environment_optimizations(save)
                console.print("✅ [green]Environment optimizations applied[/green]")
                logger.info("config_action_completed", action="set", apply_env=True, save=save)
            elif not key or value is None:
                console.print("❌ [red]Key and value required for set action[/red]")
                console.print("💡 Use: python main.py config set <key> <value>")
                logger.error("config_action_failed", action="set", reason="missing_key_or_value")
                raise typer.Exit(1)
            else:
                # Parse value based on type
                parsed_value = value
                original_type = "string"
                if value.lower() in ['true', 'false']:
                    parsed_value = value.lower() == 'true'
                    original_type = "boolean"
                elif value.isdigit():
                    parsed_value = int(value)
                    original_type = "integer"
                elif value.replace('.', '').isdigit():
                    try:
                        parsed_value = float(value)
                        original_type = "float"
                    except ValueError:
                        pass
                        
                config_manager.set_setting(key, parsed_value, save)
                console.print(f"✅ [green]Set {key} = {parsed_value}[/green]")
                logger.info("config_action_completed", action="set", key=key, value=str(parsed_value), 
                           original_value=value, parsed_type=original_type, save=save)
                
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
            
            # Count total settings for logging
            def _count_settings(data):
                count = 0
                for value in data.values():
                    if isinstance(value, dict):
                        count += _count_settings(value)
                    else:
                        count += 1
                return count
            
            setting_count = _count_settings(settings)
            logger.info("config_action_completed", action="list", section=section, setting_count=setting_count)
            
        elif action == "reset":
            if section:
                console.print(f"🔄 [yellow]Resetting {section} section to defaults...[/yellow]")
                config_manager.reset_config(section)
                console.print(f"✅ [green]{section.title()} section reset to defaults[/green]")
                logger.info("config_action_completed", action="reset", section=section)
            else:
                console.print("🔄 [yellow]Resetting entire configuration to defaults...[/yellow]")
                config_manager.reset_config()
                console.print("✅ [green]Configuration reset to defaults[/green]")
                logger.info("config_action_completed", action="reset", section="all")
                
        elif action == "export":
            if not file_path:
                # Generate default filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = f"hdi_config_{timestamp}.{format}"
                
            config_manager.export_config(Path(file_path), format)
            console.print(f"📤 [green]Configuration exported to {file_path}[/green]")
            logger.info("config_action_completed", action="export", file_path=file_path, format=format)
            
        elif action == "import":
            if not file_path:
                console.print("❌ [red]File path required for import action[/red]")
                console.print("💡 Use: python main.py config import --file <path>")
                logger.error("config_action_failed", action="import", reason="missing_file_path")
                raise typer.Exit(1)
                
            if not Path(file_path).exists():
                console.print(f"❌ [red]File not found: {file_path}[/red]")
                logger.error("config_action_failed", action="import", file_path=file_path, reason="file_not_found")
                raise typer.Exit(1)
                
            config_manager.import_config(Path(file_path), merge=True, save=save)
            console.print(f"📥 [green]Configuration imported from {file_path}[/green]")
            logger.info("config_action_completed", action="import", file_path=file_path, save=save)
            
        elif action == "validate":
            errors = config_manager.validate_config()
            if errors:
                console.print("❌ [red]Configuration validation failed:[/red]\n")
                for error in errors:
                    console.print(f"  • [red]{error}[/red]")
                logger.error("config_action_failed", action="validate", error_count=len(errors), errors=errors)
                raise typer.Exit(1)
            else:
                console.print("✅ [green]Configuration is valid[/green]")
                logger.info("config_action_completed", action="validate", status="valid")
                
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
            logger.info("config_action_completed", action="environment", **env_info)
            
        else:
            console.print(f"❌ [red]Unknown action: {action}[/red]")
            console.print("💡 Valid actions: get, set, list, reset, export, import, validate, environment")
            logger.error("config_action_failed", action=action, reason="unknown_action")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"❌ [red]Configuration error: {e}[/red]")
        logger.error("config_action_failed", action=action, error=str(e), error_type=type(e).__name__)
        raise typer.Exit(1)


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
    🖥️  Launch live status dashboard with real-time monitoring.
    
    Displays a continuous real-time dashboard with system metrics,
    active operations, and operation queue status.
    
    Examples:
        python main.py status-dashboard                    # Standard dashboard
        python main.py status-dashboard --refresh-rate 5.0 # Slower refresh
        python main.py status-dashboard --no-system        # Hide system metrics
        python main.py status-dashboard --no-queue         # Hide queue panel
    """
    logger.info("command_started", command="status_dashboard", refresh_rate=refresh_rate, 
                show_system=show_system, show_queue=show_queue, user="cli")
    console.print("🖥️  [bold cyan]Starting Live Status Dashboard[/bold cyan]")
    console.print(f"📊 Refresh Rate: {refresh_rate} Hz")
    console.print("⏹️  Press Ctrl+C to exit\n")
    
    try:
        # Import the LiveStatusDashboard class
        dashboard = LiveStatusDashboard(
            refresh_rate=refresh_rate,
            show_system_metrics=show_system,
            show_operation_queue=show_queue
        )
        
        logger.info("status_dashboard_starting", refresh_rate=refresh_rate)
        # Start the dashboard (this will run until Ctrl+C)
        dashboard.start()
        
    except KeyboardInterrupt:
        console.print("\n👋 [green]Dashboard stopped by user[/green]")
        logger.info("status_dashboard_stopped", stop_reason="user_interrupt")
        
    except Exception as e:
        console.print(f"\n❌ [red]Dashboard error: {e}[/red]")
        console.print("💡 [blue]Use 'python main.py troubleshoot status-dashboard' for help[/blue]")
        logger.error("command_failed", command="status_dashboard", error=str(e), error_type=type(e).__name__)
        raise typer.Exit(1)