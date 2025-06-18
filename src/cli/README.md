# CLI Module

The CLI module provides a user-friendly command-line interface for the Historical Data Ingestor, built with Rich for beautiful terminal output and comprehensive error handling. It supports data ingestion, querying, and system management operations.

## Architecture

### Core Components

- **Command Structure**: Hierarchical command organization with clear help documentation
- **Rich Integration**: Beautiful terminal output with colors, tables, and progress bars
- **Error Handling**: Comprehensive error boundaries with helpful error messages
- **Parameter Validation**: Robust input validation with suggestions for corrections
- **Progress Tracking**: Real-time progress indicators for long-running operations

## Available Commands

### Main Entry Point (`main.py`)

The primary CLI entry point provides access to all system functionality:

```bash
# Basic usage
python main.py --help

# Available commands:
python main.py query      # Query historical data
python main.py ingest     # Ingest data from APIs
python main.py list-jobs  # List available ingestion jobs
python main.py status     # Check system status
python main.py version    # Display version information
```

### Query Command (`query`)

Powerful querying interface with flexible output options:

```bash
# Basic query
python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31

# Multiple symbols
python main.py query --symbols ES.c.0,NQ.c.0 --start-date 2024-01-01 --end-date 2024-01-31

# Different output formats
python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31 --output-format csv
python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31 --output-format json

# Save to file
python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31 --output-file data.csv

# Query specific schema
python main.py query -s ES.c.0 --schema trades --start-date 2024-01-01 --end-date 2024-01-01

# Limit results
python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31 --limit 1000
```

**Query Parameters:**
- `--symbols, -s`: Security symbols (comma-separated or multiple flags)
- `--start-date, -sd`: Start date (YYYY-MM-DD format)
- `--end-date, -ed`: End date (YYYY-MM-DD format)
- `--schema`: Data schema (ohlcv-1d, trades, tbbo, statistics, definitions)
- `--output-format, -f`: Output format (table, csv, json)
- `--output-file, -o`: Output file path (optional)
- `--limit`: Limit number of results (optional)

### Ingest Command (`ingest`)

Data ingestion from configured API sources:

```bash
# Basic ingestion
python main.py ingest --api databento

# Specific job configuration
python main.py ingest --api databento --job daily_ohlcv

# Custom date range
python main.py ingest --api databento --start-date 2024-01-01 --end-date 2024-01-31

# Specific symbols
python main.py ingest --api databento --symbols ES.c.0,NQ.c.0

# Use predefined job
python main.py ingest --api databento --job ohlcv_1d

# Custom job with specific parameters
python main.py ingest --api databento --dataset GLBX.MDP3 --schema ohlcv-1d --symbols CL.FUT,ES.FUT --start-date 2023-01-01 --end-date 2023-12-31
```

**Ingest Parameters:**
- `--api`: API provider (currently supports: databento)
- `--job`: Predefined job name from configuration
- `--dataset`: Dataset identifier (e.g., GLBX.MDP3)
- `--schema`: Schema type (e.g., ohlcv-1d, trades, tbbo)
- `--symbols`: Comma-separated symbols (e.g., CL.FUT,ES.FUT)
- `--start-date`: Start date (YYYY-MM-DD)
- `--end-date`: End date (YYYY-MM-DD)
- `--stype-in`: Symbol type (continuous, native, parent)
- `--force`: Force execution without confirmation

### Status Command

System health and status monitoring:

```bash
# Check system status and connectivity
python main.py status
```

### List Jobs Command

List available predefined ingestion jobs:

```bash
# List jobs for default API (databento)
python main.py list-jobs

# List jobs for specific API
python main.py list-jobs --api databento
```

**List Jobs Parameters:**
- `--api`: API type to list jobs for (default: databento)

### Version Command

Display version information:

```bash
# Show version information
python main.py version
```

## Rich Terminal Output

### Table Formatting

The CLI uses Rich tables for beautiful data display:

```python
from rich.table import Table
from rich.console import Console

def display_ohlcv_data(data):
    """Display OHLCV data in a Rich table"""
    table = Table(title="OHLCV Data")
    
    # Add columns with styling
    table.add_column("Timestamp", style="cyan", no_wrap=True)
    table.add_column("Symbol", style="green")
    table.add_column("Open", style="yellow", justify="right")
    table.add_column("High", style="red", justify="right")
    table.add_column("Low", style="blue", justify="right")
    table.add_column("Close", style="yellow", justify="right")
    table.add_column("Volume", style="magenta", justify="right")
    
    # Add data rows
    for record in data:
        table.add_row(
            record["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            record["symbol"],
            f"${record['open_price']:,.2f}",
            f"${record['high_price']:,.2f}",
            f"${record['low_price']:,.2f}",
            f"${record['close_price']:,.2f}",
            f"{record['volume']:,}"
        )
    
    console = Console()
    console.print(table)
```

### Progress Bars

Real-time progress tracking for long operations:

```python
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

def show_ingestion_progress(total_records):
    """Display ingestion progress with Rich progress bar"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("[blue]{task.completed}/{task.total} records"),
    ) as progress:
        
        task = progress.add_task("Ingesting data...", total=total_records)
        
        for completed in process_data():
            progress.update(task, completed=completed)
```

### Status Displays

Colorized status information:

```python
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

def display_system_status(status_data):
    """Display system status with Rich formatting"""
    console = Console()
    
    # Database status
    db_status = "✅ Connected" if status_data["database"] else "❌ Failed"
    db_color = "green" if status_data["database"] else "red"
    
    # API status  
    api_status = "✅ Configured" if status_data["api_key"] else "❌ Missing"
    api_color = "green" if status_data["api_key"] else "red"
    
    # Create status panel
    status_text = Text()
    status_text.append("Database: ", style="bold")
    status_text.append(db_status, style=db_color)
    status_text.append("\nAPI Key: ", style="bold")
    status_text.append(api_status, style=api_color)
    
    panel = Panel(status_text, title="System Status", border_style="blue")
    console.print(panel)
```

## Error Handling and User Experience

### Input Validation

Comprehensive validation with helpful suggestions:

```python
from datetime import datetime
from rich.console import Console
import difflib

def validate_symbol(symbol, available_symbols):
    """Validate symbol with suggestions for typos"""
    if symbol in available_symbols:
        return True
        
    # Find close matches
    close_matches = difflib.get_close_matches(symbol, available_symbols, n=3, cutoff=0.6)
    
    console = Console()
    console.print(f"[red]Error: Symbol '{symbol}' not found[/red]")
    
    if close_matches:
        console.print("[yellow]Did you mean one of these?[/yellow]")
        for match in close_matches:
            console.print(f"  • {match}")
    
    return False

def validate_date_range(start_date, end_date):
    """Validate date range with helpful error messages"""
    console = Console()
    
    if start_date > end_date:
        console.print("[red]Error: Start date must be before end date[/red]")
        return False
        
    if end_date > datetime.now().date():
        console.print("[yellow]Warning: End date is in the future[/yellow]")
        console.print("Only historical data is available")
        
    # Check for very large date ranges
    days_diff = (end_date - start_date).days
    if days_diff > 365:
        console.print(f"[yellow]Warning: Large date range ({days_diff} days)[/yellow]")
        console.print("This query may take a long time and use significant resources")
        
        if not click.confirm("Do you want to continue?"):
            return False
            
    return True
```

### Error Messages

User-friendly error messages with actionable suggestions:

```python
def handle_database_error(error):
    """Handle database connection errors with helpful messages"""
    console = Console()
    
    if "connection refused" in str(error).lower():
        console.print("[red]❌ Database Connection Failed[/red]")
        console.print("\n[yellow]Troubleshooting steps:[/yellow]")
        console.print("1. Check if TimescaleDB is running:")
        console.print("   [cyan]docker-compose ps[/cyan]")
        console.print("2. Verify environment variables:")
        console.print("   [cyan]printenv | grep POSTGRES[/cyan]")
        console.print("3. Test database connectivity:")
        console.print("   [cyan]python main.py status --component database[/cyan]")
        
    elif "authentication failed" in str(error).lower():
        console.print("[red]❌ Database Authentication Failed[/red]")
        console.print("\n[yellow]Check your credentials:[/yellow]")
        console.print("• POSTGRES_USER")
        console.print("• POSTGRES_PASSWORD")
        console.print("• POSTGRES_HOST")
        console.print("• POSTGRES_PORT")

def handle_api_error(error, api_name):
    """Handle API errors with specific guidance"""
    console = Console()
    
    if "unauthorized" in str(error).lower():
        console.print(f"[red]❌ {api_name} API Authentication Failed[/red]")
        console.print(f"\n[yellow]Check your {api_name.upper()}_API_KEY:[/yellow]")
        console.print("1. Verify the API key is correct")
        console.print("2. Check if the key has expired")
        console.print("3. Ensure proper permissions")
        
    elif "rate limit" in str(error).lower():
        console.print(f"[red]❌ {api_name} API Rate Limit Exceeded[/red]")
        console.print("\n[yellow]Wait and retry:[/yellow]")
        console.print("• The request will automatically retry")
        console.print("• Consider reducing batch size")
        console.print("• Check your API usage limits")
```

## Command Implementation Examples

### Query Command Implementation

```python
import click
from rich.console import Console
from rich.table import Table
from datetime import datetime, date

@click.command()
@click.option('--symbols', '-s', multiple=True, required=True, help='Security symbols')
@click.option('--start-date', '-sd', type=click.DateTime(formats=['%Y-%m-%d']), required=True)
@click.option('--end-date', '-ed', type=click.DateTime(formats=['%Y-%m-%d']), required=True) 
@click.option('--schema', default='ohlcv-1d', help='Data schema')
@click.option('--output-format', '-f', type=click.Choice(['table', 'csv', 'json']), default='table')
@click.option('--output-file', '-o', help='Output file path')
@click.option('--limit', type=int, help='Limit number of results')
def query(symbols, start_date, end_date, schema, output_format, output_file, limit):
    """Query historical financial data"""
    console = Console()
    
    try:
        # Convert datetime objects to date
        start_date = start_date.date()
        end_date = end_date.date()
        
        # Validate inputs
        if not validate_date_range(start_date, end_date):
            return
            
        # Process symbols
        symbol_list = []
        for symbol_input in symbols:
            symbol_list.extend([s.strip() for s in symbol_input.split(',')])
        
        # Initialize query builder
        with QueryBuilder() as qb:
            # Validate symbols
            for symbol in symbol_list:
                if not validate_symbol(symbol, qb.get_available_symbols()):
                    return
            
            # Execute query based on schema
            if schema.startswith('ohlcv'):
                results = qb.query_daily_ohlcv(
                    symbols=symbol_list,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit
                )
            elif schema == 'trades':
                results = qb.query_trades(
                    symbols=symbol_list,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit
                )
            else:
                console.print(f"[red]Unsupported schema: {schema}[/red]")
                return
            
            # Output results
            if output_format == 'table':
                display_results_table(results, schema)
            elif output_format == 'csv':
                export_csv(results, output_file)
            elif output_format == 'json':
                export_json(results, output_file)
                
            console.print(f"\n[green]✅ Query completed: {len(results)} records[/green]")
            
    except Exception as e:
        handle_query_error(e)
```

### Status Command Implementation

```python
@click.command()
@click.option('--detailed', is_flag=True, help='Show detailed status')
@click.option('--component', help='Check specific component')
def status(detailed, component):
    """Check system status and health"""
    console = Console()
    
    console.print("🔍 Checking system status...", style="blue")
    
    # Perform health checks
    health_status = perform_health_checks(component)
    
    # Display results
    display_health_status(health_status, detailed)
    
    # System information
    if detailed:
        display_system_info()

def perform_health_checks(component=None):
    """Perform comprehensive health checks"""
    checks = {
        "database": check_database_connectivity,
        "api": check_api_configuration,
        "filesystem": check_filesystem_access,
        "configuration": check_configuration_validity
    }
    
    if component:
        if component in checks:
            return {component: checks[component]()}
        else:
            raise click.BadParameter(f"Unknown component: {component}")
    
    # Run all checks
    results = {}
    for name, check_func in checks.items():
        try:
            results[name] = check_func()
        except Exception as e:
            results[name] = {"status": "error", "error": str(e)}
    
    return results
```

## CLI Extension Patterns

### Adding New Commands

```python
# 1. Create command file: src/cli/commands/new_command.py
@click.command()
@click.option('--parameter', help='Command parameter')
def new_command(parameter):
    """Description of new command"""
    console = Console()
    console.print(f"Executing new command with parameter: {parameter}")

# 2. Register in main CLI: src/cli/cli.py
from .commands.new_command import new_command

cli.add_command(new_command)

# 3. Add tests: tests/unit/cli/test_new_command.py
def test_new_command():
    result = runner.invoke(new_command, ['--parameter', 'test'])
    assert result.exit_code == 0
```

### Custom Output Formatters

```python
class OutputFormatter:
    """Base class for output formatters"""
    
    def format(self, data, schema):
        raise NotImplementedError

class JSONFormatter(OutputFormatter):
    def format(self, data, schema):
        import json
        from decimal import Decimal
        
        def decimal_serializer(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        return json.dumps(data, default=decimal_serializer, indent=2)

class CSVFormatter(OutputFormatter):
    def format(self, data, schema):
        import csv
        import io
        
        if not data:
            return ""
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue()
```

## Best Practices

### Command Design
- Use clear, descriptive command names
- Provide comprehensive help text
- Implement input validation with helpful error messages
- Support common use cases with sensible defaults

### User Experience
- Use Rich for beautiful terminal output
- Provide progress indicators for long operations
- Include confirmation prompts for destructive operations
- Offer suggestions for common mistakes

### Error Handling
- Catch and handle specific error types
- Provide actionable error messages
- Include troubleshooting steps in error output
- Log detailed errors while showing user-friendly messages

### Performance
- Stream large result sets instead of loading all in memory
- Provide options to limit output size
- Show progress for long-running operations
- Allow users to cancel operations gracefully 