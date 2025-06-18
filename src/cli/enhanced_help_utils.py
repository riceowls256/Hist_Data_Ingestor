"""
Enhanced help utilities for the CLI with interactive features.

Provides comprehensive help text, interactive menus, guided workflows,
and enhanced examples for better user experience.
"""

from typing import Dict, List, Optional, Tuple, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.tree import Tree
from rich.columns import Columns
from rich.syntax import Syntax
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path

console = Console()


def get_command_prefix() -> str:
    """Detect the command being used (hdi, python main.py, etc.)."""
    # Priority 1: Check environment variable (can be set in shell profile)
    if os.environ.get('HDI_COMMAND_PREFIX'):
        return os.environ.get('HDI_COMMAND_PREFIX')
    
    # Priority 2: Check for .hdi_config file in home directory
    config_file = Path.home() / '.hdi_config'
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                content = f.read().strip()
                if content:
                    return content
        except:
            pass
    
    # Priority 3: Try to detect from process info
    # When using an alias, the parent process might show the alias command
    try:
        # Check if we can detect hdi in the command that started this process
        import subprocess
        # Try to get the parent process command on macOS/Linux
        if sys.platform in ['darwin', 'linux']:
            try:
                # Get parent PID
                ppid = os.getppid()
                # Get parent command
                result = subprocess.run(['ps', '-p', str(ppid), '-o', 'comm='], 
                                      capture_output=True, text=True)
                if result.returncode == 0 and 'hdi' in result.stdout:
                    return "hdi"
            except:
                pass
    except:
        pass
    
    # Priority 4: Check if running through hdi in argv
    if sys.argv[0].endswith('hdi') or 'hdi' in sys.argv[0]:
        return "hdi"
    
    # Priority 5: Since user is clearly using hdi (they ran "hdi quickstart"),
    # and we can't detect it automatically, just default to hdi for better UX
    # The worst case is they need to adjust the command slightly
    return "hdi"


class InteractiveHelpMenu:
    """Interactive help menu system for navigating documentation."""
    
    HELP_CATEGORIES = {
        "1": {
            "title": "🚀 Getting Started",
            "description": "New to the system? Start here!",
            "items": [
                ("Environment Setup", "setup_environment"),
                ("Your First Ingestion", "first_ingestion"),
                ("Basic Queries", "basic_queries"),
                ("Understanding Schemas", "schema_overview"),
            ]
        },
        "2": {
            "title": "📊 Data Ingestion",
            "description": "Learn how to ingest different data types",
            "items": [
                ("OHLCV Data", "ingest_ohlcv"),
                ("Trades Data", "ingest_trades"),
                ("Quote Data (TBBO)", "ingest_tbbo"),
                ("Market Statistics", "ingest_statistics"),
                ("Batch Operations", "batch_ingestion"),
            ]
        },
        "3": {
            "title": "🔍 Querying Data",
            "description": "Extract and analyze your data",
            "items": [
                ("Basic Queries", "query_basics"),
                ("Advanced Filters", "query_advanced"),
                ("Export Options", "query_export"),
                ("Performance Tips", "query_performance"),
                ("Symbol Resolution", "symbol_resolution"),
            ]
        },
        "4": {
            "title": "🎯 Common Workflows",
            "description": "End-to-end examples for common tasks",
            "items": [
                ("Daily Market Analysis", "workflow_daily"),
                ("Historical Research", "workflow_research"),
                ("Backtesting Data Prep", "workflow_backtest"),
                ("Multi-Asset Analysis", "workflow_multi_asset"),
            ]
        },
        "5": {
            "title": "🔧 Troubleshooting",
            "description": "Solutions to common problems",
            "items": [
                ("Connection Issues", "trouble_connection"),
                ("Symbol Errors", "trouble_symbols"),
                ("Performance Issues", "trouble_performance"),
                ("Data Quality", "trouble_quality"),
            ]
        },
        "6": {
            "title": "📚 Reference",
            "description": "Quick reference and cheat sheets",
            "items": [
                ("Command Reference", "ref_commands"),
                ("Symbol Formats", "ref_symbols"),
                ("Date Formats", "ref_dates"),
                ("Schema Fields", "ref_schemas"),
            ]
        }
    }
    
    @classmethod
    def show_menu(cls):
        """Display the interactive help menu."""
        while True:
            console.clear()
            console.print("\n[bold cyan]📖 Historical Data Ingestor - Interactive Help[/bold cyan]\n")
            
            # Display categories
            for key, category in cls.HELP_CATEGORIES.items():
                console.print(f"[bold yellow]{key}.[/bold yellow] {category['title']}")
                console.print(f"   [dim]{category['description']}[/dim]")
            
            console.print("\n[bold yellow]0.[/bold yellow] Exit Help")
            
            choice = Prompt.ask("\n[cyan]Select a category[/cyan]", default="0")
            
            if choice == "0":
                break
            elif choice in cls.HELP_CATEGORIES:
                cls.show_category(choice)
            else:
                console.print("[red]Invalid choice. Please try again.[/red]")
                console.input("Press Enter to continue...")
    
    @classmethod
    def show_category(cls, category_key: str):
        """Display items in a category."""
        category = cls.HELP_CATEGORIES[category_key]
        
        while True:
            console.clear()
            console.print(f"\n[bold cyan]{category['title']}[/bold cyan]")
            console.print(f"[dim]{category['description']}[/dim]\n")
            
            for i, (title, _) in enumerate(category['items'], 1):
                console.print(f"[bold yellow]{i}.[/bold yellow] {title}")
            
            console.print("\n[bold yellow]0.[/bold yellow] Back to Main Menu")
            
            choice = Prompt.ask("\n[cyan]Select a topic[/cyan]", default="0")
            
            if choice == "0":
                break
            elif choice.isdigit() and 1 <= int(choice) <= len(category['items']):
                item_index = int(choice) - 1
                _, method_name = category['items'][item_index]
                cls.show_help_content(method_name)
            else:
                console.print("[red]Invalid choice. Please try again.[/red]")
                console.input("Press Enter to continue...")
    
    @classmethod
    def show_help_content(cls, content_key: str):
        """Display specific help content."""
        content_map = {
            "setup_environment": cls._help_setup_environment,
            "first_ingestion": cls._help_first_ingestion,
            "basic_queries": cls._help_basic_queries,
            "schema_overview": cls._help_schema_overview,
            "ingest_ohlcv": cls._help_ingest_ohlcv,
            "ingest_trades": cls._help_ingest_trades,
            "ingest_tbbo": cls._help_ingest_tbbo,
            "ingest_statistics": cls._help_ingest_statistics,
            "batch_ingestion": cls._help_batch_ingestion,
            "query_basics": cls._help_query_basics,
            "query_advanced": cls._help_query_advanced,
            "query_export": cls._help_query_export,
            "query_performance": cls._help_query_performance,
            "symbol_resolution": cls._help_symbol_resolution,
            "workflow_daily": cls._help_workflow_daily,
            "workflow_research": cls._help_workflow_research,
            "workflow_backtest": cls._help_workflow_backtest,
            "workflow_multi_asset": cls._help_workflow_multi_asset,
            "trouble_connection": cls._help_trouble_connection,
            "trouble_symbols": cls._help_trouble_symbols,
            "trouble_performance": cls._help_trouble_performance,
            "trouble_quality": cls._help_trouble_quality,
            "ref_commands": cls._help_ref_commands,
            "ref_symbols": cls._help_ref_symbols,
            "ref_dates": cls._help_ref_dates,
            "ref_schemas": cls._help_ref_schemas,
        }
        
        console.clear()
        if content_key in content_map:
            content_map[content_key]()
        else:
            console.print(f"[red]Help content for '{content_key}' not found.[/red]")
        
        console.print("\n[dim]Press Enter to continue...[/dim]")
        console.input()
    
    @staticmethod
    def _help_setup_environment():
        """Environment setup help."""
        console.print("[bold cyan]Environment Setup[/bold cyan]\n")
        
        steps = [
            ("1. Create .env file", "cp .env.example .env"),
            ("2. Add your API key", "DATABENTO_API_KEY=your-actual-key"),
            ("3. Configure database", "TIMESCALE_HOST=localhost\nTIMESCALE_PORT=5432\nTIMESCALE_DB=market_data\nTIMESCALE_USER=postgres\nTIMESCALE_PASSWORD=password"),
            ("4. Start services", "docker-compose up -d"),
            ("5. Verify setup", "python main.py status"),
        ]
        
        for step, code in steps:
            console.print(f"\n[yellow]{step}:[/yellow]")
            if "\n" in code:
                for line in code.split("\n"):
                    console.print(f"  [green]{line}[/green]")
            else:
                console.print(f"  [green]{code}[/green]")
        
        console.print("\n[bold]Troubleshooting:[/bold]")
        console.print("• If database connection fails, check Docker is running")
        console.print("• For API errors, verify your Databento key is valid")
        console.print("• Use 'python main.py troubleshoot' for detailed help")
    
    @staticmethod
    def _help_first_ingestion():
        """First ingestion help."""
        console.print("[bold cyan]Your First Data Ingestion[/bold cyan]\n")
        
        console.print("Let's start with a simple example to ingest one day of S&P 500 futures data:\n")
        
        # Detect command prefix
        cmd_prefix = get_command_prefix()
        
        code = f'''# Step 1: Check available predefined jobs
{cmd_prefix} list-jobs --api databento

# Step 2: Run a predefined job (easiest way)
{cmd_prefix} ingest --api databento --job ohlcv_1d

# Step 3: Or specify custom parameters
{cmd_prefix} ingest --api databento \\
    --dataset GLBX.MDP3 \\
    --schema ohlcv-1d \\
    --symbols ES.c.0 \\
    --start-date 2024-01-15 \\
    --end-date 2024-01-15'''
        
        syntax = Syntax(code, "bash", theme="monokai", line_numbers=True)
        console.print(syntax)
        
        console.print("\n[bold]What happens during ingestion:[/bold]")
        console.print("1. Connects to Databento API")
        console.print("2. Downloads data for specified symbols and dates")
        console.print("3. Transforms data to standardized format")
        console.print("4. Validates data quality")
        console.print("5. Stores in TimescaleDB")
        
        console.print("\n[yellow]💡 Tip:[/yellow] Start with single days of OHLCV data to test your setup")
    
    @staticmethod
    def _help_basic_queries():
        """Basic queries help."""
        console.print("[bold cyan]Basic Data Queries[/bold cyan]\n")
        
        console.print("Query your ingested data with these examples:\n")
        
        cmd_prefix = get_command_prefix()
        
        examples = [
            ("Simple OHLCV query", f'''{cmd_prefix} query -s ES.c.0 \\
    --start-date 2024-01-01 \\
    --end-date 2024-01-31'''),
            
            ("Multiple symbols", f'''{cmd_prefix} query \\
    --symbols ES.c.0,NQ.c.0,CL.c.0 \\
    --start-date 2024-01-01 \\
    --end-date 2024-01-31'''),
            
            ("Export to CSV", f'''{cmd_prefix} query -s ES.c.0 \\
    --start-date 2024-01-01 \\
    --end-date 2024-01-31 \\
    --output-format csv \\
    --output-file results.csv'''),
            
            ("Preview without running", f'''{cmd_prefix} query -s ES.c.0 \\
    --start-date 2024-01-01 \\
    --end-date 2024-01-31 \\
    --dry-run'''),
        ]
        
        for title, code in examples:
            console.print(f"\n[yellow]{title}:[/yellow]")
            syntax = Syntax(code, "bash", theme="monokai")
            console.print(syntax)
        
        console.print("\n[bold]Output Formats:[/bold]")
        console.print("• table - Human-readable terminal output (default)")
        console.print("• csv - Excel-compatible comma-separated values")
        console.print("• json - Machine-readable JSON format")
    
    @staticmethod
    def _help_schema_overview():
        """Schema overview help."""
        console.print("[bold cyan]Understanding Data Schemas[/bold cyan]\n")
        
        schemas = [
            ("OHLCV-1D", "Daily price bars", "Best for daily analysis and charting", 
             ["open_price", "high_price", "low_price", "close_price", "volume"]),
            ("Trades", "Individual transactions", "Best for order flow and microstructure",
             ["price", "size", "side", "conditions", "ts_event"]),
            ("TBBO", "Top bid/ask quotes", "Best for spread analysis and market depth",
             ["bid_px", "ask_px", "bid_sz", "ask_sz", "bid_ct", "ask_ct"]),
            ("Statistics", "Market metrics", "Best for open interest and settlements",
             ["stat_type", "price", "quantity", "update_action"]),
            ("Definitions", "Contract specs", "Best for understanding instruments",
             ["asset_class", "exchange", "tick_size", "min_price_increment"]),
        ]
        
        for name, desc, use_case, fields in schemas:
            console.print(f"\n[bold yellow]{name}[/bold yellow]")
            console.print(f"Description: {desc}")
            console.print(f"Use case: {use_case}")
            console.print("Key fields:")
            for field in fields:
                console.print(f"  • {field}")
        
        console.print(f"\n[yellow]💡 Tip:[/yellow] Use '{get_command_prefix()} schemas' for a quick reference table")


class QuickstartWizard:
    """Interactive wizard for new users to set up their first pipeline."""
    
    @classmethod
    def run(cls):
        """Run the quickstart wizard."""
        console.print("\n[bold cyan]🚀 Historical Data Ingestor - Quick Start Wizard[/bold cyan]\n")
        console.print("This wizard will help you set up your first data pipeline.\n")
        
        # Step 1: Check environment
        if not cls._check_environment():
            return
        
        # Step 2: Select data type
        schema = cls._select_schema()
        
        # Step 3: Select symbol
        symbol = cls._select_symbol(schema)
        
        # Step 4: Select date range
        start_date, end_date = cls._select_date_range(schema)
        
        # Step 5: Confirm and run
        cls._confirm_and_run(schema, symbol, start_date, end_date)
    
    @classmethod
    def _check_environment(cls) -> bool:
        """Check if environment is properly configured."""
        console.print("[bold yellow]Step 1: Checking Environment[/bold yellow]\n")
        
        checks = []
        
        # Check API key
        api_key = os.getenv('DATABENTO_API_KEY')
        if api_key:
            checks.append(("Databento API Key", "✅ Configured", True))
        else:
            checks.append(("Databento API Key", "❌ Not found", False))
        
        # Check database config
        db_host = os.getenv('TIMESCALE_HOST', 'localhost')
        checks.append(("Database Host", f"✅ {db_host}", True))
        
        # Display results
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Component")
        table.add_column("Status")
        
        all_good = True
        for component, status, ok in checks:
            table.add_row(component, status)
            if not ok:
                all_good = False
        
        console.print(table)
        
        if not all_good:
            console.print("\n[red]❌ Some components are not configured.[/red]")
            console.print("Please run 'python main.py troubleshoot' for help.\n")
            return False
        
        console.print("\n[green]✅ Environment is properly configured![/green]\n")
        return True
    
    @classmethod
    def _select_schema(cls) -> str:
        """Let user select a schema type."""
        console.print("[bold yellow]Step 2: Select Data Type[/bold yellow]\n")
        
        schemas = [
            ("1", "ohlcv-1d", "Daily OHLCV (Recommended for beginners)", "~100 KB/symbol/year"),
            ("2", "trades", "Individual Trades", "~1-10 GB/symbol/day"),
            ("3", "tbbo", "Top Bid/Offer Quotes", "~500 MB/symbol/day"),
            ("4", "statistics", "Market Statistics", "~10 MB/symbol/month"),
        ]
        
        for num, schema, desc, size in schemas:
            console.print(f"[yellow]{num}.[/yellow] {desc}")
            console.print(f"   [dim]Schema: {schema}, Typical size: {size}[/dim]")
        
        choice = Prompt.ask("\n[cyan]Select data type[/cyan]", choices=["1", "2", "3", "4"], default="1")
        
        schema_map = {"1": "ohlcv-1d", "2": "trades", "3": "tbbo", "4": "statistics"}
        selected = schema_map[choice]
        
        console.print(f"\n[green]Selected: {selected}[/green]\n")
        return selected
    
    @classmethod
    def _select_symbol(cls, schema: str) -> str:
        """Let user select a symbol."""
        console.print("[bold yellow]Step 3: Select Symbol[/bold yellow]\n")
        
        popular_symbols = [
            ("1", "ES.c.0", "S&P 500 E-mini Futures (Continuous)"),
            ("2", "NQ.c.0", "Nasdaq 100 E-mini Futures (Continuous)"),
            ("3", "CL.c.0", "Crude Oil Futures (Continuous)"),
            ("4", "GC.c.0", "Gold Futures (Continuous)"),
            ("5", "6E.c.0", "Euro FX Futures (Continuous)"),
            ("0", "custom", "Enter custom symbol"),
        ]
        
        console.print("Popular symbols:")
        for num, symbol, desc in popular_symbols:
            if num != "0":
                console.print(f"[yellow]{num}.[/yellow] {symbol} - {desc}")
        console.print(f"\n[yellow]0.[/yellow] Enter custom symbol")
        
        choice = Prompt.ask("\n[cyan]Select symbol[/cyan]", default="1")
        
        if choice == "0":
            symbol = Prompt.ask("[cyan]Enter symbol (e.g., ES.c.0)[/cyan]")
        else:
            symbol_map = {opt[0]: opt[1] for opt in popular_symbols if opt[0] != "0"}
            symbol = symbol_map.get(choice, "ES.c.0")
        
        console.print(f"\n[green]Selected: {symbol}[/green]\n")
        return symbol
    
    @classmethod
    def _select_date_range(cls, schema: str) -> Tuple[str, str]:
        """Let user select date range."""
        console.print("[bold yellow]Step 4: Select Date Range[/bold yellow]\n")
        
        today = datetime.now()
        
        if schema in ["trades", "tbbo"]:
            console.print("[yellow]Note: High-frequency data can be large. Starting with a single day.[/yellow]\n")
            
            # For high-frequency data, suggest single day
            suggestions = [
                ("1", "Yesterday", (today - timedelta(days=1)).strftime("%Y-%m-%d"), 
                 (today - timedelta(days=1)).strftime("%Y-%m-%d")),
                ("2", "Last Friday", cls._last_friday(), cls._last_friday()),
                ("3", "Custom date", None, None),
            ]
        else:
            # For daily data, suggest longer ranges
            suggestions = [
                ("1", "Last 7 days", (today - timedelta(days=7)).strftime("%Y-%m-%d"), 
                 today.strftime("%Y-%m-%d")),
                ("2", "Last 30 days", (today - timedelta(days=30)).strftime("%Y-%m-%d"), 
                 today.strftime("%Y-%m-%d")),
                ("3", "Year to date", f"{today.year}-01-01", today.strftime("%Y-%m-%d")),
                ("4", "Custom range", None, None),
            ]
        
        for num, desc, start, end in suggestions:
            if start:
                console.print(f"[yellow]{num}.[/yellow] {desc} ({start} to {end})")
            else:
                console.print(f"[yellow]{num}.[/yellow] {desc}")
        
        choice = Prompt.ask("\n[cyan]Select date range[/cyan]", default="1")
        
        if choice in ["3", "4"] or not any(s[0] == choice for s in suggestions):
            start_date = Prompt.ask("[cyan]Enter start date (YYYY-MM-DD)[/cyan]")
            end_date = Prompt.ask("[cyan]Enter end date (YYYY-MM-DD)[/cyan]")
        else:
            for num, _, start, end in suggestions:
                if num == choice:
                    start_date, end_date = start, end
                    break
        
        console.print(f"\n[green]Selected: {start_date} to {end_date}[/green]\n")
        return start_date, end_date
    
    @classmethod
    def _last_friday(cls) -> str:
        """Get the date of the last Friday."""
        today = datetime.now()
        days_since_friday = (today.weekday() - 4) % 7
        if days_since_friday == 0:
            days_since_friday = 7
        last_friday = today - timedelta(days=days_since_friday)
        return last_friday.strftime("%Y-%m-%d")
    
    @classmethod
    def _confirm_and_run(cls, schema: str, symbol: str, start_date: str, end_date: str):
        """Confirm settings and generate commands."""
        console.print("[bold yellow]Step 5: Review and Run[/bold yellow]\n")
        
        # Display summary
        summary = Table(show_header=True, header_style="bold magenta")
        summary.add_column("Setting")
        summary.add_column("Value")
        
        summary.add_row("Data Type", schema)
        summary.add_row("Symbol", symbol)
        summary.add_row("Date Range", f"{start_date} to {end_date}")
        
        console.print(summary)
        
        # Detect the command being used (hdi alias or python main.py)
        import sys
        cmd_prefix = "python main.py"
        
        # Check if running via an alias or custom command
        if sys.argv[0].endswith('hdi') or 'hdi' in sys.argv[0]:
            cmd_prefix = "hdi"
        elif os.path.basename(sys.argv[0]) != 'main.py':
            # Using some other custom setup
            cmd_prefix = os.path.basename(sys.argv[0])
        
        # Generate commands
        console.print("\n[bold cyan]Generated Commands:[/bold cyan]\n")
        
        console.print("[bold red]⚠️  IMPORTANT: Copy each command as a SINGLE LINE![/bold red]")
        console.print("[yellow]The commands below are long but must be pasted as one line.[/yellow]\n")
        
        # Ingestion command - single line format for easier copying
        # Add stype_in parameter for statistics schema
        stype_param = ""
        if schema == "statistics":
            # For statistics, we need to specify the symbol type
            # Using 'continuous' for c.0 symbols
            stype_param = " --stype-in continuous"
        
        ingest_cmd = f'{cmd_prefix} ingest --api databento --dataset GLBX.MDP3 --schema {schema} --symbols {symbol} --start-date {start_date} --end-date {end_date}{stype_param}'
        
        console.print("[yellow]1. Ingest data:[/yellow]")
        console.print("[bold]Copy this entire line:[/bold]")
        console.print(f"[green]{ingest_cmd}[/green]")
        
        # Note about multi-line format
        console.print("\n[dim]Note: You can also split long commands with \\ but must copy ALL lines together:[/dim]")
        stype_line = f" \\\n    --stype-in continuous" if schema == "statistics" else ""
        ingest_cmd_multiline = f'''{cmd_prefix} ingest --api databento \\
    --dataset GLBX.MDP3 \\
    --schema {schema} \\
    --symbols {symbol} \\
    --start-date {start_date} \\
    --end-date {end_date}{stype_line}'''
        
        syntax = Syntax(ingest_cmd_multiline, "bash", theme="monokai")
        console.print(syntax)
        
        # Query command - single line
        query_cmd = f'{cmd_prefix} query -s {symbol} --schema {schema} --start-date {start_date} --end-date {end_date}'
        
        console.print("\n[yellow]2. Query ingested data:[/yellow]")
        console.print("[bold]Copy this entire line:[/bold]")
        console.print(f"[green]{query_cmd}[/green]")
        
        # Export command - single line
        export_cmd = f'{cmd_prefix} query -s {symbol} --schema {schema} --start-date {start_date} --end-date {end_date} --output-format csv --output-file {symbol.replace(".", "_")}_{schema}_export.csv'
        
        console.print("\n[yellow]3. Export to CSV:[/yellow]")
        console.print("[bold]Copy this entire line:[/bold]")
        console.print(f"[green]{export_cmd}[/green]")
        
        console.print("\n[green]✅ Setup complete![/green]")
        console.print("\n[bold]Instructions:[/bold]")
        console.print("1. [bold cyan]Triple-click[/bold cyan] on a green command line to select the entire line")
        console.print("2. [bold cyan]Copy[/bold cyan] the selected line (Cmd+C on Mac)")
        console.print("3. [bold cyan]Paste[/bold cyan] into your terminal (Cmd+V on Mac)")
        console.print("4. [bold cyan]Press Enter[/bold cyan] to run the command")
        
        console.print("\n[yellow]⚠️  Common Issue:[/yellow]")
        console.print("If you see 'command not found: --symbols' or similar errors:")
        console.print("  • You copied the command with line breaks")
        console.print("  • Make sure to copy the ENTIRE green line as one piece")
        console.print("  • Don't copy the multi-line version unless you know how to handle \\")
        
        console.print(f"\n[yellow]💡 Need help?[/yellow] Use '{cmd_prefix} help-menu' for detailed guidance")


class WorkflowExamples:
    """Provides complete workflow examples for common use cases."""
    
    WORKFLOWS = {
        "daily_analysis": {
            "title": "Daily Market Analysis Workflow",
            "description": "Download and analyze yesterday's market data",
            "steps": [
                {
                    "name": "Check system status",
                    "command": "python main.py status",
                    "explanation": "Verify database and API connections"
                },
                {
                    "name": "Ingest yesterday's OHLCV data",
                    "command": '''python main.py ingest --api databento \\
    --schema ohlcv-1d \\
    --symbols "ES.c.0,NQ.c.0,CL.c.0,GC.c.0" \\
    --start-date {yesterday} \\
    --end-date {yesterday}''',
                    "explanation": "Download daily bars for major futures"
                },
                {
                    "name": "Query and visualize",
                    "command": '''python main.py query \\
    --symbols "ES.c.0,NQ.c.0,CL.c.0,GC.c.0" \\
    --start-date {last_30_days} \\
    --end-date {yesterday} \\
    --output-format csv \\
    --output-file daily_analysis.csv''',
                    "explanation": "Export last 30 days for analysis"
                },
                {
                    "name": "Check for anomalies",
                    "command": '''python main.py query \\
    --symbols "ES.c.0,NQ.c.0,CL.c.0,GC.c.0" \\
    --start-date {yesterday} \\
    --end-date {yesterday} \\
    --schema statistics''',
                    "explanation": "Review volume and open interest changes"
                }
            ]
        },
        "historical_research": {
            "title": "Historical Research Workflow", 
            "description": "Collect data for backtesting or research",
            "steps": [
                {
                    "name": "List available jobs",
                    "command": "python main.py list-jobs --api databento",
                    "explanation": "See predefined configurations"
                },
                {
                    "name": "Ingest historical OHLCV",
                    "command": '''python main.py ingest --api databento \\
    --schema ohlcv-1d \\
    --symbols ES.c.0 \\
    --start-date 2023-01-01 \\
    --end-date 2023-12-31''',
                    "explanation": "Download full year of daily data"
                },
                {
                    "name": "Ingest key events data",
                    "command": '''python main.py ingest --api databento \\
    --schema statistics \\
    --symbols ES.c.0 \\
    --start-date 2023-01-01 \\
    --end-date 2023-12-31 \\
    --stype_in "settlement,open_interest"''',
                    "explanation": "Get settlement prices and open interest"
                },
                {
                    "name": "Export for analysis",
                    "command": '''python main.py query -s ES.c.0 \\
    --start-date 2023-01-01 \\
    --end-date 2023-12-31 \\
    --output-format json \\
    --output-file es_2023_full.json''',
                    "explanation": "Export in JSON for programmatic access"
                }
            ]
        },
        "intraday_analysis": {
            "title": "Intraday Analysis Workflow",
            "description": "Analyze high-frequency trades and quotes",
            "steps": [
                {
                    "name": "Ingest trades data",
                    "command": '''python main.py ingest --api databento \\
    --schema trades \\
    --symbols ES.c.0 \\
    --start-date {last_trading_day} \\
    --end-date {last_trading_day}''',
                    "explanation": "Download all trades for analysis"
                },
                {
                    "name": "Ingest quote data",
                    "command": '''python main.py ingest --api databento \\
    --schema tbbo \\
    --symbols ES.c.0 \\
    --start-date {last_trading_day} \\
    --end-date {last_trading_day}''',
                    "explanation": "Download top-of-book quotes"
                },
                {
                    "name": "Query trades by hour",
                    "command": '''python main.py query -s ES.c.0 \\
    --schema trades \\
    --start-date {last_trading_day} \\
    --end-date {last_trading_day} \\
    --limit 10000 \\
    --output-format csv''',
                    "explanation": "Export trades for spread analysis"
                },
                {
                    "name": "Analyze bid-ask spreads",
                    "command": '''python main.py query -s ES.c.0 \\
    --schema tbbo \\
    --start-date {last_trading_day} \\
    --end-date {last_trading_day} \\
    --limit 10000''',
                    "explanation": "Review quote data for liquidity analysis"
                }
            ]
        }
    }
    
    @classmethod
    def show_workflow(cls, workflow_name: Optional[str] = None):
        """Display workflow examples."""
        if workflow_name and workflow_name in cls.WORKFLOWS:
            cls._display_single_workflow(workflow_name)
        else:
            cls._display_workflow_menu()
    
    @classmethod
    def _display_workflow_menu(cls):
        """Display menu of available workflows."""
        console.print("\n[bold cyan]📋 Available Workflows[/bold cyan]\n")
        
        for key, workflow in cls.WORKFLOWS.items():
            console.print(f"[bold yellow]{workflow['title']}[/bold yellow]")
            console.print(f"[dim]{workflow['description']}[/dim]")
            console.print(f"Usage: python main.py workflows {key}\n")
    
    @classmethod
    def _display_single_workflow(cls, workflow_name: str):
        """Display a specific workflow."""
        workflow = cls.WORKFLOWS[workflow_name]
        
        console.print(f"\n[bold cyan]{workflow['title']}[/bold cyan]")
        console.print(f"[dim]{workflow['description']}[/dim]\n")
        
        # Detect command prefix
        import sys
        cmd_prefix = "python main.py"
        if sys.argv[0].endswith('hdi') or 'hdi' in sys.argv[0]:
            cmd_prefix = "hdi"
        elif os.path.basename(sys.argv[0]) != 'main.py':
            cmd_prefix = os.path.basename(sys.argv[0])
        
        # Calculate dynamic dates
        today = datetime.now()
        yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        last_30_days = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        last_trading_day = cls._get_last_trading_day().strftime("%Y-%m-%d")
        
        replacements = {
            "{yesterday}": yesterday,
            "{last_30_days}": last_30_days,
            "{last_trading_day}": last_trading_day,
            "{today}": today.strftime("%Y-%m-%d"),
            "python main.py": cmd_prefix,  # Replace command prefix
        }
        
        for i, step in enumerate(workflow['steps'], 1):
            console.print(f"[bold yellow]Step {i}: {step['name']}[/bold yellow]")
            console.print(f"[dim]{step['explanation']}[/dim]")
            
            # Replace placeholders in command
            command = step['command']
            for placeholder, value in replacements.items():
                command = command.replace(placeholder, value)
            
            syntax = Syntax(command, "bash", theme="monokai")
            console.print(syntax)
            console.print()
    
    @classmethod
    def _get_last_trading_day(cls) -> datetime:
        """Get the last trading day (skip weekends)."""
        today = datetime.now()
        offset = 1
        
        # If today is Monday, last trading day was Friday
        if today.weekday() == 0:
            offset = 3
        # If today is Sunday, last trading day was Friday
        elif today.weekday() == 6:
            offset = 2
            
        return today - timedelta(days=offset)


class CheatSheet:
    """Provides a quick reference cheat sheet."""
    
    @classmethod
    def display(cls):
        """Display the cheat sheet."""
        console.print("\n[bold cyan]📄 Historical Data Ingestor - Cheat Sheet[/bold cyan]\n")
        
        sections = [
            cls._common_commands(),
            cls._query_shortcuts(),
            cls._date_examples(),
            cls._symbol_formats(),
        ]
        
        # Display in columns for better layout
        console.print(Columns(sections, equal=True, expand=True))
        
        console.print("\n[bold yellow]Pro Tips:[/bold yellow]")
        console.print("• Use --dry-run to preview commands without execution")
        console.print("• Add --validate-only to check parameters")
        console.print("• Use -s multiple times for multiple symbols")
        console.print("• Pipe query output to less for pagination: | less")
        console.print("• Set DATABENTO_API_KEY in .env to avoid typing it")
    
    @staticmethod
    def _common_commands() -> Panel:
        """Common commands section."""
        cmd = get_command_prefix()
        content = f"""[bold yellow]Common Commands[/bold yellow]

[green]# System[/green]
{cmd} status
{cmd} version
{cmd} help-menu

[green]# Ingestion[/green]
{cmd} ingest --api databento --job ohlcv_1d
{cmd} list-jobs --api databento

[green]# Querying[/green]  
{cmd} query -s ES.c.0 --start-date 2024-01-01
{cmd} schemas
{cmd} symbols"""
        
        return Panel(content, border_style="cyan")
    
    @staticmethod
    def _query_shortcuts() -> Panel:
        """Query shortcuts section."""
        content = """[bold yellow]Query Shortcuts[/bold yellow]

[green]# Output formats[/green]
--output-format table (default)
--output-format csv -o file.csv
--output-format json

[green]# Useful flags[/green]
--dry-run         # Preview only
--validate-only   # Check params
--limit 1000      # Limit results

[green]# Multiple symbols[/green]
-s ES.c.0 -s NQ.c.0
--symbols "ES.c.0,NQ.c.0" """
        
        return Panel(content, border_style="cyan")
    
    @staticmethod
    def _date_examples() -> Panel:
        """Date examples section."""
        today = datetime.now()
        yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        last_week = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        last_month = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        
        content = f"""[bold yellow]Date Examples[/bold yellow]

[green]# Format: YYYY-MM-DD[/green]
--start-date {yesterday}
--end-date {today.strftime("%Y-%m-%d")}

[green]# Common ranges[/green]
Yesterday: {yesterday}
Last week: {last_week}
Last month: {last_month}
YTD: {today.year}-01-01

[green]# Same day[/green]
--start-date {yesterday} --end-date {yesterday}"""
        
        return Panel(content, border_style="cyan")
    
    @staticmethod
    def _symbol_formats() -> Panel:
        """Symbol formats section."""
        content = """[bold yellow]Symbol Formats[/bold yellow]

[green]# Continuous contracts[/green]
ES.c.0  # S&P 500 E-mini
NQ.c.0  # Nasdaq 100
CL.c.0  # Crude Oil
GC.c.0  # Gold

[green]# Futures[/green]
ES.FUT  # All ES contracts
CLZ23   # Specific contract

[green]# Options[/green]
ES.OPT  # All ES options

[green]# Multiple[/green]
"ES.c.0,NQ.c.0,CL.c.0" """
        
        return Panel(content, border_style="cyan")


class SymbolHelper:
    """Helper for symbol discovery and information."""
    
    COMMON_SYMBOLS = {
        "Equity Indices": [
            ("ES", "S&P 500 E-mini", "ES.c.0"),
            ("NQ", "Nasdaq 100 E-mini", "NQ.c.0"),
            ("RTY", "Russell 2000 E-mini", "RTY.c.0"),
            ("YM", "Dow Jones E-mini", "YM.c.0"),
        ],
        "Energy": [
            ("CL", "Crude Oil WTI", "CL.c.0"),
            ("NG", "Natural Gas", "NG.c.0"),
            ("RB", "RBOB Gasoline", "RB.c.0"),
            ("HO", "Heating Oil", "HO.c.0"),
        ],
        "Metals": [
            ("GC", "Gold", "GC.c.0"),
            ("SI", "Silver", "SI.c.0"),
            ("HG", "Copper", "HG.c.0"),
            ("PL", "Platinum", "PL.c.0"),
        ],
        "Agriculture": [
            ("ZC", "Corn", "ZC.c.0"),
            ("ZS", "Soybeans", "ZS.c.0"),
            ("ZW", "Wheat", "ZW.c.0"),
            ("ZL", "Soybean Oil", "ZL.c.0"),
        ],
        "Currencies": [
            ("6E", "Euro FX", "6E.c.0"),
            ("6B", "British Pound", "6B.c.0"),
            ("6J", "Japanese Yen", "6J.c.0"),
            ("6C", "Canadian Dollar", "6C.c.0"),
        ],
        "Fixed Income": [
            ("ZN", "10-Year T-Note", "ZN.c.0"),
            ("ZB", "30-Year T-Bond", "ZB.c.0"),
            ("ZF", "5-Year T-Note", "ZF.c.0"),
            ("ZT", "2-Year T-Note", "ZT.c.0"),
        ]
    }
    
    @classmethod
    def show_symbols(cls, category: Optional[str] = None, search: Optional[str] = None):
        """Display available symbols."""
        console.print("\n[bold cyan]📈 Symbol Reference[/bold cyan]\n")
        
        if search:
            cls._search_symbols(search)
        elif category:
            cls._show_category(category)
        else:
            cls._show_all_categories()
    
    @classmethod
    def _show_all_categories(cls):
        """Show all symbol categories."""
        console.print("Available symbol categories:\n")
        
        for i, category in enumerate(cls.COMMON_SYMBOLS.keys(), 1):
            console.print(f"[bold yellow]{i}.[/bold yellow] {category}")
            
            # Show first few symbols as preview
            symbols = cls.COMMON_SYMBOLS[category][:3]
            preview = ", ".join([s[0] for s in symbols])
            console.print(f"   [dim]{preview}, ...[/dim]")
        
        console.print("\n[yellow]Usage:[/yellow]")
        console.print("• python main.py symbols --category 'Energy'")
        console.print("• python main.py symbols --search 'oil'")
    
    @classmethod
    def _show_category(cls, category: str):
        """Show symbols in a specific category."""
        # Find category (case-insensitive)
        found_category = None
        for cat in cls.COMMON_SYMBOLS.keys():
            if cat.lower() == category.lower():
                found_category = cat
                break
        
        if not found_category:
            console.print(f"[red]Category '{category}' not found.[/red]")
            console.print("Available categories:", ", ".join(cls.COMMON_SYMBOLS.keys()))
            return
        
        console.print(f"[bold yellow]{found_category} Symbols:[/bold yellow]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Code")
        table.add_column("Name")
        table.add_column("Continuous Symbol")
        table.add_column("Example Query")
        
        for code, name, symbol in cls.COMMON_SYMBOLS[found_category]:
            example = f"query -s {symbol}"
            table.add_row(code, name, symbol, example)
        
        console.print(table)
    
    @classmethod
    def _search_symbols(cls, search_term: str):
        """Search for symbols matching a term."""
        search_lower = search_term.lower()
        results = []
        
        for category, symbols in cls.COMMON_SYMBOLS.items():
            for code, name, symbol in symbols:
                if (search_lower in code.lower() or 
                    search_lower in name.lower() or
                    search_lower in symbol.lower()):
                    results.append((category, code, name, symbol))
        
        if results:
            console.print(f"[bold yellow]Found {len(results)} symbols matching '{search_term}':[/bold yellow]\n")
            
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Category")
            table.add_column("Code")
            table.add_column("Name")
            table.add_column("Symbol")
            
            for category, code, name, symbol in results:
                table.add_row(category, code, name, symbol)
            
            console.print(table)
        else:
            console.print(f"[red]No symbols found matching '{search_term}'.[/red]")


class GuidedMode:
    """Provides guided mode for commands with interactive prompts."""
    
    @classmethod
    def guided_ingest(cls) -> Dict[str, Any]:
        """Guide user through ingestion parameters."""
        console.print("\n[bold cyan]🎯 Guided Ingestion Mode[/bold cyan]\n")
        
        params = {}
        
        # API selection (currently only databento)
        params['api'] = 'databento'
        console.print("[green]✓ API: databento[/green]")
        
        # Check for predefined job
        use_job = Confirm.ask("\nWould you like to use a predefined job?", default=True)
        
        if use_job:
            # List jobs and let user select
            console.print("\nFetching available jobs...")
            params['job'] = cls._select_job()
            return params
        
        # Manual configuration
        console.print("\n[yellow]Manual Configuration[/yellow]")
        
        # Dataset
        params['dataset'] = Prompt.ask(
            "\nDataset", 
            default="GLBX.MDP3",
            choices=["GLBX.MDP3", "XNAS.ITCH", "OPRA.PILLAR"]
        )
        
        # Schema
        schema_choices = ["ohlcv-1d", "trades", "tbbo", "statistics", "definitions"]
        params['schema'] = Prompt.ask(
            "\nSchema type",
            choices=schema_choices,
            default="ohlcv-1d"
        )
        
        # Symbols
        console.print("\n[dim]Enter symbols (comma-separated, e.g., ES.c.0,NQ.c.0)[/dim]")
        symbols_input = Prompt.ask("Symbols", default="ES.c.0")
        params['symbols'] = symbols_input
        
        # Date range
        params['start_date'] = cls._get_date("Start date")
        params['end_date'] = cls._get_date("End date", default_days_back=0)
        
        # Schema-specific parameters
        if params['schema'] == 'statistics':
            params['stype_in'] = Prompt.ask(
                "\nStatistic types (optional)",
                default="",
                show_default=False
            )
        
        return params
    
    @classmethod
    def guided_query(cls) -> Dict[str, Any]:
        """Guide user through query parameters."""
        console.print("\n[bold cyan]🎯 Guided Query Mode[/bold cyan]\n")
        
        params = {}
        
        # Symbols
        console.print("[dim]Enter symbols to query (comma-separated)[/dim]")
        symbols_input = Prompt.ask("Symbols", default="ES.c.0")
        params['symbols'] = symbols_input.split(',')
        
        # Schema
        schema_choices = ["ohlcv-1d", "trades", "tbbo", "statistics", "definitions"]
        params['schema'] = Prompt.ask(
            "\nSchema type",
            choices=schema_choices,
            default="ohlcv-1d"
        )
        
        # Date range
        params['start_date'] = cls._get_date("Start date", default_days_back=30)
        params['end_date'] = cls._get_date("End date", default_days_back=0)
        
        # Output format
        params['output_format'] = Prompt.ask(
            "\nOutput format",
            choices=["table", "csv", "json"],
            default="table"
        )
        
        if params['output_format'] in ["csv", "json"]:
            params['output_file'] = Prompt.ask(
                "Output filename",
                default=f"query_results.{params['output_format']}"
            )
        
        # Limit for high-frequency data
        if params['schema'] in ["trades", "tbbo"]:
            use_limit = Confirm.ask(
                "\nLimit results? (recommended for large datasets)",
                default=True
            )
            if use_limit:
                params['limit'] = IntPrompt.ask("Result limit", default=1000)
        
        # Dry run option
        params['dry_run'] = Confirm.ask(
            "\nPreview query without executing?",
            default=False
        )
        
        return params
    
    @classmethod
    def _select_job(cls) -> str:
        """Let user select from available jobs."""
        # This would normally fetch from config
        jobs = [
            ("ohlcv_1d", "Daily OHLCV for major futures"),
            ("intraday_es", "ES intraday trades and quotes"),
            ("commodity_daily", "Daily commodity futures"),
        ]
        
        console.print("\nAvailable jobs:")
        for i, (job_id, desc) in enumerate(jobs, 1):
            console.print(f"[yellow]{i}.[/yellow] {job_id} - {desc}")
        
        choice = IntPrompt.ask("\nSelect job", min=1, max=len(jobs))
        return jobs[choice - 1][0]
    
    @classmethod
    def _get_date(cls, prompt: str, default_days_back: int = 1) -> str:
        """Get date input with validation."""
        default_date = (datetime.now() - timedelta(days=default_days_back)).strftime("%Y-%m-%d")
        
        while True:
            date_str = Prompt.ask(f"\n{prompt} (YYYY-MM-DD)", default=default_date)
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                return date_str
            except ValueError:
                console.print("[red]Invalid date format. Please use YYYY-MM-DD.[/red]")


# Export the enhanced utilities
__all__ = [
    'InteractiveHelpMenu',
    'QuickstartWizard',
    'WorkflowExamples',
    'CheatSheet',
    'SymbolHelper',
    'GuidedMode',
]