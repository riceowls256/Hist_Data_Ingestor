"""
Help Commands Module

This module contains all help-related CLI commands including examples,
troubleshooting, tips, schemas, quickstart wizard, and interactive help menu.
"""

from typing import Optional

import typer
from rich.console import Console

from cli.help_utils import (
    CLITroubleshooter, show_examples, show_tips,
    format_schema_help
)
from cli.enhanced_help_utils import (
    InteractiveHelpMenu, QuickstartWizard, CheatSheet
)
from utils.custom_logger import get_logger

# Initialize Rich console and logging
console = Console()
logger = get_logger(__name__)

# Create Typer app for help commands
app = typer.Typer(
    name="help",
    help="Help and documentation commands (examples, troubleshoot, tips, quickstart)",
    no_args_is_help=False
)


@app.command()
def examples(
    command: Optional[str] = typer.Argument(
        None,
        help="Specific command to show examples for (ingest, query, status, list-jobs)"
    )
):
    """
    Show practical examples for CLI commands.
    
    Examples:
        python main.py examples              # Show all examples
        python main.py examples query        # Show query examples only
        python main.py examples ingest       # Show ingestion examples
    """
    show_examples(command)


@app.command()
def troubleshoot(
    error: Optional[str] = typer.Argument(
        None,
        help="Error message or keyword to get specific help"
    )
):
    """
    Get troubleshooting help for common issues.
    
    Examples:
        python main.py troubleshoot                    # Show common issues
        python main.py troubleshoot "database error"   # Get database help
        python main.py troubleshoot "symbol not found" # Symbol resolution help
    """
    if error:
        console.print(f"\n🔍 [bold cyan]Troubleshooting: {error}[/bold cyan]\n")
        CLITroubleshooter.show_help(error)
    else:
        console.print("\n🔧 [bold cyan]Common Issues and Solutions:[/bold cyan]\n")
        for _, issue_data in CLITroubleshooter.COMMON_ISSUES.items():
            console.print(f"[bold yellow]{issue_data['title']}:[/bold yellow]")
            console.print(f"  Error patterns: {', '.join(issue_data['error_patterns'][:2])}...")
            console.print(f"  Solution: {issue_data['solutions'][0]}")
            console.print()


@app.command()
def tips(
    category: Optional[str] = typer.Argument(
        None,
        help="Category of tips to show (performance, quality, efficiency, troubleshooting)"
    )
):
    """
    Show usage tips and best practices.
    
    Examples:
        python main.py tips                  # Show all tips
        python main.py tips performance      # Performance optimization tips
        python main.py tips troubleshooting  # Troubleshooting tips
    """
    show_tips(category)


@app.command()
def schemas():
    """
    Display available data schemas and their fields.
    
    Shows detailed information about each schema type including:
    - Schema name and description
    - Key fields and their meanings
    - Common use cases
    """
    console.print("\n📊 [bold cyan]Available Data Schemas[/bold cyan]\n")
    table = format_schema_help()
    console.print(table)
    console.print("\n💡 [yellow]Use --schema parameter with query or ingest commands[/yellow]")
    console.print("Example: python main.py query -s ES.c.0 --schema trades")


@app.command("help-menu")
def help_menu():
    """
    Launch interactive help menu system.
    
    Provides an interactive, navigable help system with categories:
    - Getting Started
    - Data Ingestion
    - Querying Data
    - Common Workflows
    - Troubleshooting
    - Reference
    """
    InteractiveHelpMenu.show_menu()


@app.command()
def quickstart():
    """
    Interactive setup wizard for new users.
    
    Guides you through:
    - Environment verification
    - Choosing data type
    - Selecting symbols
    - Setting date ranges
    - Generating ready-to-use commands
    """
    QuickstartWizard.run()


@app.command()
def cheatsheet():
    """
    Display quick reference cheat sheet.
    
    Shows:
    - Common commands
    - Query shortcuts
    - Date format examples
    - Symbol format reference
    - Pro tips for efficient usage
    """
    CheatSheet.display()