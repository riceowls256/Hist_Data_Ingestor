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
        monitor_instance = OperationMonitor()
        monitor_instance.cleanup_old_operations(cleanup_days)
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
        monitor_instance = OperationMonitor()
        history_ops = monitor_instance.get_operation_history(limit=20)
        
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
        monitor_instance = OperationMonitor()
        if operation_id in monitor_instance.operations:
            operation = monitor_instance.operations[operation_id]
            
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