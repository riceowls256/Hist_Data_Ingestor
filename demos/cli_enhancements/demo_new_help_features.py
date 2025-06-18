#!/usr/bin/env python3
"""
Demo script showcasing the new enhanced CLI help features.

This script demonstrates all the new help commands and features added to improve
user experience and make the CLI more accessible to new users.
"""

import subprocess
import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()


def run_command(cmd: str, description: str):
    """Run a CLI command and display its purpose."""
    console.print(f"\n[bold yellow]Demo: {description}[/bold yellow]")
    console.print(f"[cyan]Command:[/cyan] {cmd}")
    console.print("[dim]Press Enter to run this command...[/dim]")
    input()
    
    # Run the command
    subprocess.run(cmd, shell=True)
    
    console.print("\n[dim]Press Enter to continue to next demo...[/dim]")
    input()


def main():
    """Run through all the new help feature demos."""
    console.print(Panel.fit(
        "[bold cyan]Historical Data Ingestor - Enhanced Help Features Demo[/bold cyan]\n\n"
        "This demo will showcase all the new help commands and features:\n"
        "• Interactive help menu\n"
        "• Quickstart wizard\n"
        "• Workflow examples\n"
        "• Symbol discovery\n"
        "• Cheat sheet\n"
        "• Guided mode for commands",
        border_style="cyan"
    ))
    
    demos = [
        # Basic help commands
        ("python main.py --help", "Show main help with new commands"),
        
        # Interactive help menu
        ("python main.py help-menu", "Launch interactive help menu system"),
        
        # Quickstart wizard
        ("python main.py quickstart", "Run quickstart wizard for new users"),
        
        # Workflow examples
        ("python main.py workflows", "List available workflow examples"),
        ("python main.py workflows daily_analysis", "Show daily analysis workflow"),
        
        # Symbol helper
        ("python main.py symbols", "Browse symbol categories"),
        ("python main.py symbols --category Energy", "Show energy sector symbols"),
        ("python main.py symbols --search gold", "Search for gold-related symbols"),
        
        # Cheat sheet
        ("python main.py cheatsheet", "Display quick reference cheat sheet"),
        
        # Enhanced examples
        ("python main.py examples", "Show all command examples"),
        ("python main.py examples query", "Show query-specific examples"),
        
        # Guided mode demos
        ("python main.py query --guided", "Query with interactive guided mode"),
        ("python main.py ingest --guided", "Ingest with interactive guided mode"),
        
        # Tips and troubleshooting
        ("python main.py tips", "Show usage tips"),
        ("python main.py troubleshoot", "Show troubleshooting guide"),
        ("python main.py troubleshoot 'symbol not found'", "Get specific error help"),
    ]
    
    console.print("\n[bold]Available Demos:[/bold]")
    for i, (cmd, desc) in enumerate(demos, 1):
        console.print(f"{i:2d}. {desc}")
    
    console.print("\n[yellow]You can run specific demos or all of them.[/yellow]")
    choice = Prompt.ask("Enter demo numbers (comma-separated) or 'all'", default="all")
    
    if choice.lower() == "all":
        selected_demos = demos
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(",")]
            selected_demos = [(demos[i][0], demos[i][1]) for i in indices if 0 <= i < len(demos)]
        except:
            console.print("[red]Invalid selection. Running all demos.[/red]")
            selected_demos = demos
    
    for cmd, description in selected_demos:
        try:
            run_command(cmd, description)
        except KeyboardInterrupt:
            console.print("\n[yellow]Demo interrupted. Moving to next...[/yellow]")
            continue
        except Exception as e:
            console.print(f"\n[red]Error running demo: {e}[/red]")
            continue
    
    console.print(Panel.fit(
        "[bold green]Demo Complete![/bold green]\n\n"
        "The CLI now provides comprehensive help features including:\n"
        "✅ Interactive help menu for easy navigation\n"
        "✅ Quickstart wizard for new users\n"
        "✅ Guided mode for complex commands\n"
        "✅ Complete workflow examples\n"
        "✅ Symbol discovery and search\n"
        "✅ Quick reference cheat sheet\n\n"
        "Users can now easily learn and use the system!",
        border_style="green"
    ))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo cancelled by user.[/yellow]")
        sys.exit(0)