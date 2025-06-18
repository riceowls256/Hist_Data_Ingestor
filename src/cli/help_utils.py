"""
Help utilities for the CLI.

Provides comprehensive help text, examples, troubleshooting guidance,
and parameter validation helpers for the CLI commands.
"""

from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from datetime import datetime, timedelta

console = Console()


class CLIExamples:
    """Provides example commands for each CLI operation."""
    
    INGEST_EXAMPLES = {
        "basic": {
            "description": "Basic daily OHLCV ingestion for a single symbol",
            "command": "python main.py ingest --api databento --job ohlcv_1d",
            "notes": "Uses predefined job configuration from config file"
        },
        "custom": {
            "description": "Custom ingestion with specific parameters",
            "command": """python main.py ingest --api databento --dataset GLBX.MDP3 \\
    --schema ohlcv-1d --symbols ES.FUT,CL.FUT \\
    --start-date 2024-01-01 --end-date 2024-01-31""",
            "notes": "Overrides default parameters for custom data range"
        },
        "multi_symbol": {
            "description": "Ingest multiple symbols with trades data",
            "command": """python main.py ingest --api databento --schema trades \\
    --symbols "ES.c.0,NQ.c.0,CL.c.0" \\
    --start-date 2024-01-15 --end-date 2024-01-15""",
            "notes": "Trades data can be large - consider using single day ranges"
        },
        "statistics": {
            "description": "Ingest market statistics data",
            "command": """python main.py ingest --api databento --schema statistics \\
    --symbols ES.c.0 --start-date 2024-01-01 \\
    --end-date 2024-01-31 --stype_in continuous""",
            "notes": "Statistics include open interest, settlement prices, etc."
        },
        "custom_job": {
            "description": "Custom ingestion (without predefined job)",
            "command": """python main.py ingest --api databento --dataset GLBX.MDP3 \\
    --schema ohlcv-1d --symbols ES.c.0,CL.c.0 \\
    --start-date 2024-01-01 --end-date 2024-01-31""",
            "notes": "Custom jobs auto-generate names like 'cli_ohlcv-1d_ES.c.0_CL.c.0'"
        }
    }
    
    QUERY_EXAMPLES = {
        "basic": {
            "description": "Query daily OHLCV data with table output",
            "command": """python main.py query -s ES.c.0 \\
    --start-date 2024-01-01 --end-date 2024-01-31""",
            "notes": "Default output format is table, default schema is ohlcv-1d"
        },
        "multi_symbol": {
            "description": "Query multiple symbols with CSV output",
            "command": """python main.py query --symbols ES.c.0,NQ.c.0 \\
    --start-date 2024-01-01 --end-date 2024-01-31 \\
    --output-format csv --output-file results.csv""",
            "notes": "Symbols can be comma-separated or use multiple -s flags"
        },
        "trades": {
            "description": "Query trades data with limit",
            "command": """python main.py query -s ES.c.0 --schema trades \\
    --start-date 2024-01-15 --end-date 2024-01-15 \\
    --limit 1000 --output-format json""",
            "notes": "Use limit to control result size for high-frequency data"
        },
        "tbbo": {
            "description": "Query top-of-book bid/offer data",
            "command": """python main.py query -s CL.c.0 --schema tbbo \\
    --start-date 2024-01-15 --end-date 2024-01-15 \\
    --limit 500""",
            "notes": "TBBO data shows best bid/ask prices and sizes"
        },
        "definitions": {
            "description": "Query instrument definitions",
            "command": """python main.py query -s ES.c.0 --schema definitions \\
    --start-date 2024-01-01 --end-date 2024-01-31""",
            "notes": "Definitions include contract specifications and metadata"
        }
    }
    
    STATUS_EXAMPLES = {
        "basic": {
            "description": "Check system status",
            "command": "python main.py status",
            "notes": "Shows database connectivity, API configuration, and system health"
        }
    }
    
    LIST_JOBS_EXAMPLES = {
        "basic": {
            "description": "List available predefined jobs",
            "command": "python main.py list-jobs --api databento",
            "notes": "Shows all configured jobs from the API config file"
        }
    }


class CLITroubleshooter:
    """Provides troubleshooting guidance for common issues."""
    
    COMMON_ISSUES = {
        "database_connection": {
            "error_patterns": ["Database connection failed", "could not connect to server", "FATAL"],
            "title": "Database Connection Issues",
            "solutions": [
                "1. Check if TimescaleDB container is running: `docker-compose ps`",
                "2. Verify database credentials in .env file",
                "3. Check database logs: `docker-compose logs timescaledb`",
                "4. Ensure port 5432 is not blocked by firewall",
                "5. Try restarting database: `docker-compose restart timescaledb`"
            ],
            "example_fix": "docker-compose up -d timescaledb"
        },
        "symbol_not_found": {
            "error_patterns": ["Symbol error", "Symbol resolution failed", "No instrument_id found"],
            "title": "Symbol Resolution Issues",
            "solutions": [
                "1. Verify symbol format (e.g., ES.c.0 for continuous contracts)",
                "2. Check if symbol data has been ingested",
                "3. Use 'python main.py query --list-symbols' to see available symbols",
                "4. Ensure definitions data is loaded for the symbol",
                "5. Check date range - symbol might not have data for those dates"
            ],
            "example_fix": "python main.py ingest --api databento --schema definitions --symbols ES.c.0"
        },
        "api_authentication": {
            "error_patterns": ["API key", "Authentication failed", "401", "Unauthorized"],
            "title": "API Authentication Issues",
            "solutions": [
                "1. Check DATABENTO_API_KEY in .env file",
                "2. Verify API key is valid and not expired",
                "3. Ensure .env file is loaded: check with 'python main.py status'",
                "4. Try re-exporting the key: export DATABENTO_API_KEY='your-key'",
                "5. Check API rate limits haven't been exceeded"
            ],
            "example_fix": "echo 'DATABENTO_API_KEY=your-actual-key' >> .env"
        },
        "date_validation": {
            "error_patterns": ["Invalid date", "date must be in YYYY-MM-DD format", "ValueError"],
            "title": "Date Format Issues",
            "solutions": [
                "1. Use YYYY-MM-DD format (e.g., 2024-01-15)",
                "2. Ensure start date is before end date",
                "3. Check for typos in date values",
                "4. Don't use quotes around dates in command line",
                "5. Verify dates are not in the future"
            ],
            "example_fix": "--start-date 2024-01-01 --end-date 2024-01-31"
        },
        "no_data_found": {
            "error_patterns": ["No data found", "0 records", "Empty result"],
            "title": "No Data Retrieved",
            "solutions": [
                "1. Check if data has been ingested for the date range",
                "2. Verify symbol is correct and available",
                "3. Try a wider date range",
                "4. Check schema type matches ingested data",
                "5. Use status command to see available data ranges"
            ],
            "example_fix": "python main.py status --show-data-ranges"
        }
    }
    
    @classmethod
    def find_issue(cls, error_message: str) -> Optional[Dict]:
        """Find matching issue based on error message."""
        error_lower = error_message.lower()
        for issue_key, issue_data in cls.COMMON_ISSUES.items():
            if any(pattern.lower() in error_lower for pattern in issue_data["error_patterns"]):
                return issue_data
        return None
    
    @classmethod
    def show_help(cls, error_message: str):
        """Display troubleshooting help for an error."""
        issue = cls.find_issue(error_message)
        if issue:
            panel = Panel(
                "\n".join(issue["solutions"]),
                title=f"🔧 {issue['title']}",
                border_style="yellow"
            )
            console.print(panel)
            if issue.get("example_fix"):
                console.print(f"\n💡 Example fix: [cyan]{issue['example_fix']}[/cyan]")
        else:
            console.print("💡 [yellow]Check logs for more details: tail -f logs/app.log[/yellow]")


class CLITips:
    """Provides usage tips and best practices."""
    
    TIPS = [
        {
            "category": "Performance",
            "tips": [
                "Use --limit parameter to control result size for large queries",
                "Query single days for high-frequency data (trades, tbbo)",
                "Use CSV output format for large result sets",
                "Consider batching large date ranges into smaller chunks"
            ]
        },
        {
            "category": "Data Quality",
            "tips": [
                "Always check status before querying to ensure data availability",
                "Use --dry-run flag to preview operations before execution",
                "Monitor quarantine directory for failed records: dlq/",
                "Review logs regularly for validation warnings"
            ]
        },
        {
            "category": "Efficiency",
            "tips": [
                "Use predefined jobs for repeated ingestion tasks",
                "Export frequently used queries to scripts",
                "Use multiple -s flags or comma-separated symbols",
                "Leverage shell aliases for common commands"
            ]
        },
        {
            "category": "Troubleshooting",
            "tips": [
                "Enable verbose output with --verbose for debugging",
                "Check logs in logs/ directory for detailed errors",
                "Use 'docker-compose logs -f' to monitor services",
                "Run status command to verify system health"
            ]
        }
    ]


def show_examples(command: Optional[str] = None):
    """Display examples for CLI commands."""
    if command == "ingest":
        examples = CLIExamples.INGEST_EXAMPLES
    elif command == "query":
        examples = CLIExamples.QUERY_EXAMPLES
    elif command == "status":
        examples = CLIExamples.STATUS_EXAMPLES
    elif command == "list-jobs":
        examples = CLIExamples.LIST_JOBS_EXAMPLES
    else:
        # Show all examples
        console.print("\n[bold cyan]📚 CLI Command Examples[/bold cyan]\n")
        for cmd in ["ingest", "query", "status", "list-jobs"]:
            show_examples(cmd)
        return
    
    console.print(f"\n[bold cyan]📚 Examples for '{command}' command:[/bold cyan]\n")
    
    for key, example in examples.items():
        console.print(f"[bold yellow]{example['description']}:[/bold yellow]")
        console.print(f"[green]{example['command']}[/green]")
        if example.get('notes'):
            console.print(f"[dim]Note: {example['notes']}[/dim]")
        console.print()


def show_tips(category: Optional[str] = None):
    """Display usage tips and best practices."""
    console.print("\n[bold cyan]💡 CLI Usage Tips[/bold cyan]\n")
    
    tips_to_show = CLITips.TIPS
    if category:
        tips_to_show = [t for t in tips_to_show if t["category"].lower() == category.lower()]
    
    for tip_group in tips_to_show:
        console.print(f"[bold yellow]{tip_group['category']}:[/bold yellow]")
        for tip in tip_group["tips"]:
            console.print(f"  • {tip}")
        console.print()


def validate_date_range(start_date: str, end_date: str) -> tuple[bool, str]:
    """Validate date range and provide helpful feedback."""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        if start > end:
            return False, "Start date must be before or equal to end date"
        
        if end > datetime.now():
            return False, "End date cannot be in the future"
        
        days = (end - start).days
        if days > 365:
            return False, "Date range exceeds 365 days. Consider breaking into smaller chunks"
        
        return True, "Date range is valid"
        
    except ValueError as e:
        return False, f"Invalid date format: {e}. Use YYYY-MM-DD format"


def validate_symbols(symbols: List[str]) -> tuple[bool, str]:
    """Validate symbols and provide feedback."""
    if not symbols:
        return False, "No symbols provided"
    
    valid_patterns = [
        "Continuous contracts: XX.c.0 (e.g., ES.c.0, CL.c.0)",
        "Futures: XX.FUT (e.g., ES.FUT, CL.FUT)",
        "Options: XX.OPT (e.g., ES.OPT)"
    ]
    
    # Check for common issues
    issues = []
    for symbol in symbols:
        if " " in symbol:
            issues.append(f"Symbol '{symbol}' contains spaces")
        if not symbol:
            issues.append("Empty symbol detected")
        if len(symbol) > 20:
            issues.append(f"Symbol '{symbol}' seems too long")
    
    if issues:
        return False, "Symbol validation issues:\n" + "\n".join(issues)
    
    return True, f"Symbols appear valid. Valid patterns:\n" + "\n".join(f"  • {p}" for p in valid_patterns)


def format_schema_help() -> Table:
    """Create a table showing available schemas and their descriptions."""
    table = Table(title="Available Data Schemas", show_header=True, header_style="bold magenta")
    table.add_column("Schema", style="cyan")
    table.add_column("Description")
    table.add_column("Key Fields")
    table.add_column("Use Case")
    
    schemas = [
        ("ohlcv-1d", "Daily OHLCV bars", "open, high, low, close, volume", "Daily price analysis"),
        ("trades", "Individual trades", "price, size, side, conditions", "Trade flow analysis"),
        ("tbbo", "Top bid/offer quotes", "bid_px, ask_px, bid_sz, ask_sz", "Market depth analysis"),
        ("statistics", "Market statistics", "stat_type, stat_value, update_action", "Market metrics"),
        ("definitions", "Instrument specs", "asset, exchange, tick_size", "Contract details")
    ]
    
    for schema, desc, fields, use_case in schemas:
        table.add_row(schema, desc, fields, use_case)
    
    return table


def suggest_date_range() -> str:
    """Suggest reasonable date ranges based on current date."""
    today = datetime.now()
    suggestions = []
    
    # Last week
    last_week_start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    last_week_end = today.strftime("%Y-%m-%d")
    suggestions.append(f"Last week: --start-date {last_week_start} --end-date {last_week_end}")
    
    # Last month
    last_month_start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    suggestions.append(f"Last month: --start-date {last_month_start} --end-date {last_week_end}")
    
    # Single day (yesterday)
    yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    suggestions.append(f"Yesterday: --start-date {yesterday} --end-date {yesterday}")
    
    return "\n".join(suggestions)