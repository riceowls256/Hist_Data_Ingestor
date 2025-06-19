"""
Workflow Commands Module

This module contains workflow-related CLI commands including workflow examples,
workflow builder, and workflow management functionality.
"""

import os
import sys
from typing import Optional, List, Dict, Any
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
    from utils.custom_logger import get_logger
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
    from cli.interactive_workflows import create_interactive_workflow, WorkflowType
    from cli.common.constants import SCHEMA_MAPPING, SUPPORTED_SCHEMAS
except ImportError as e:
    # Graceful degradation for missing dependencies
    console.print(f"⚠️  [yellow]Import warning: {e}[/yellow]")
    
    # Create mock implementations for essential classes
    class MockLogger:
        def exception(self, msg): pass
        def info(self, msg, **kwargs): pass
        def warning(self, msg, **kwargs): pass
        def error(self, msg, **kwargs): pass
    
    def get_logger(name): return MockLogger()
    
    class MockWorkflowExamples:
        @staticmethod
        def show_workflow(name): 
            console.print(f"📋 [cyan]Workflow examples for: {name or 'all workflows'}[/cyan]")
    
    class MockWorkflowType:
        def __init__(self, value): self.value = value
    
    def create_interactive_workflow(workflow_type=None):
        console.print("🔧 [yellow]Interactive workflow creation not available[/yellow]")
        return None
    
    class MockEnhancedProgress:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def add_task(self, desc, total=None): return "mock_task"
        def update(self, task, **kwargs): pass
    
    # Assign mocks to globals
    WorkflowExamples = MockWorkflowExamples
    WorkflowType = MockWorkflowType
    EnhancedProgress = MockEnhancedProgress

# Initialize logging
logger = get_logger(__name__)

# Create Typer app for workflow commands
app = typer.Typer(
    name="workflow",
    help="Workflow management commands (workflows, workflow builder)",
    no_args_is_help=False
)


@app.command()
def workflows(
    workflow_name: Optional[str] = typer.Argument(
        None,
        help="Specific workflow to display (daily_analysis, historical_research, intraday_analysis)"
    )
):
    """
    Show complete workflow examples for common use cases.
    
    Available workflows:
    - daily_analysis: Daily market data analysis
    - historical_research: Collecting data for backtesting
    - intraday_analysis: High-frequency trades and quotes analysis
    
    Examples:
        python main.py workflows                    # List all workflows
        python main.py workflows daily_analysis     # Show specific workflow
    """
    logger.info("command_started", command="workflows", workflow_name=workflow_name, user="cli")
    
    try:
        WorkflowExamples.show_workflow(workflow_name)
        logger.info("command_completed", command="workflows", workflow_name=workflow_name, status="success")
        
    except Exception as e:
        console.print(f"❌ [red]Error displaying workflows: {e}[/red]")
        console.print(f"💡 [blue]Use 'python main.py troubleshoot workflows' for help[/blue]")
        logger.error("command_failed", command="workflows", workflow_name=workflow_name, 
                    error=str(e), error_type=type(e).__name__)
        raise typer.Exit(code=1)


@app.command()
def workflow(
    action: str = typer.Argument(
        ...,
        help="Action: create, list, load, run"
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name", "-n",
        help="Workflow name for load/run actions"
    ),
    workflow_type: Optional[str] = typer.Option(
        None,
        "--type", "-t",
        help="Workflow type: backfill, daily_update, multi_symbol, data_quality, custom"
    )
):
    """
    🔧 Interactive workflow builder for complex operations.
    
    Create, manage, and execute complex data processing workflows
    with step-by-step guidance and intelligent validation.
    
    Examples:
        python main.py workflow create                    # Create workflow interactively
        python main.py workflow create --type backfill   # Create specific workflow type
        python main.py workflow list                     # Show saved workflows
        python main.py workflow load --name "My Workflow"  # Load specific workflow
    """
    logger.info("command_started", command="workflow", action=action, name=name, 
                workflow_type=workflow_type, user="cli")
    
    try:
        if action == "create":
            logger.info("workflow_create_started", workflow_type=workflow_type)
            console.print("\n🔧 [bold cyan]Creating Interactive Workflow[/bold cyan]\n")
            
            workflow_type_enum = None
            if workflow_type:
                try:
                    workflow_type_enum = WorkflowType(workflow_type.lower())
                except ValueError:
                    console.print(f"❌ [red]Invalid workflow type: {workflow_type}[/red]")
                    console.print("Valid types: backfill, daily_update, multi_symbol, data_quality, custom")
                    raise typer.Exit(1)
            
            try:
                workflow = create_interactive_workflow(workflow_type_enum)
                if workflow:
                    console.print(f"\n✅ [bold green]Workflow '{workflow.name}' created successfully![/bold green]")
                    console.print(f"📋 Type: {workflow.workflow_type.value}")
                    console.print(f"📝 Steps: {len(workflow.steps)}")
                    console.print(f"💾 ID: {workflow.id}")
                    logger.info("workflow_create_success", workflow_name=workflow.name, 
                               workflow_type=workflow.workflow_type.value, step_count=len(workflow.steps))
                else:
                    console.print("\n⏹️  [yellow]Workflow creation cancelled[/yellow]")
                    logger.info("workflow_create_cancelled")
            except Exception as e:
                console.print(f"❌ [red]Failed to create workflow: {e}[/red]")
                logger.error("workflow_create_failed", error=str(e), error_type=type(e).__name__)
                raise typer.Exit(1)
        
        elif action == "list":
            logger.info("workflow_list_started")
            console.print("\n📋 [bold cyan]Saved Workflows[/bold cyan]\n")
            _list_workflows()
            logger.info("workflow_list_completed")
        
        elif action == "load":
            if not name:
                console.print("❌ [red]Workflow name is required for load action[/red]")
                console.print("💡 [blue]Use: python main.py workflow load --name 'My Workflow'[/blue]")
                logger.error("workflow_load_failed", reason="missing_name")
                raise typer.Exit(1)
            
            logger.info("workflow_load_started", workflow_name=name)
            console.print(f"\n📂 [bold cyan]Loading Workflow: {name}[/bold cyan]\n")
            _load_workflow(name)
            logger.info("workflow_load_completed", workflow_name=name)
        
        elif action == "run":
            if not name:
                console.print("❌ [red]Workflow name is required for run action[/red]")
                console.print("💡 [blue]Use: python main.py workflow run --name 'My Workflow'[/blue]")
                logger.error("workflow_run_failed", reason="missing_name")
                raise typer.Exit(1)
            
            logger.info("workflow_run_started", workflow_name=name)
            console.print(f"\n🚀 [bold cyan]Running Workflow: {name}[/bold cyan]\n")
            _run_workflow(name)
            logger.info("workflow_run_completed", workflow_name=name)
        
        else:
            console.print(f"❌ [red]Invalid action: {action}[/red]")
            console.print("Valid actions: create, list, load, run")
            logger.error("workflow_action_failed", action=action, reason="invalid_action")
            raise typer.Exit(1)
    
        logger.info("command_completed", command="workflow", action=action, status="success")
        
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"❌ [red]Workflow command failed: {e}[/red]")
        console.print(f"💡 [blue]Use 'python main.py troubleshoot workflow' for help[/blue]")
        logger.error("command_failed", command="workflow", action=action, 
                    error=str(e), error_type=type(e).__name__)
        raise typer.Exit(code=1)


def _list_workflows():
    """List all saved workflows."""
    try:
        # This would typically read from a workflows storage file/database
        # For now, show a mock example
        workflows_data = _get_mock_workflows()
        
        if not workflows_data:
            console.print("📭 [yellow]No saved workflows found[/yellow]")
            console.print("💡 [blue]Create a workflow with: python main.py workflow create[/blue]")
            return
        
        # Create table for workflow list
        table = Table(title="Saved Workflows")
        table.add_column("Name", style="bold blue")
        table.add_column("Type", style="cyan")
        table.add_column("Steps", style="green", justify="right")
        table.add_column("Created", style="dim")
        table.add_column("Status", style="magenta")
        
        for workflow in workflows_data:
            table.add_row(
                workflow["name"],
                workflow["type"],
                str(workflow["steps"]),
                workflow["created"],
                workflow["status"]
            )
        
        console.print(table)
        console.print(f"\n💡 [blue]Load a workflow with: python main.py workflow load --name 'WORKFLOW_NAME'[/blue]")
        
    except Exception as e:
        console.print(f"❌ [red]Failed to list workflows: {e}[/red]")
        logger.exception("Failed to list workflows")


def _load_workflow(name: str):
    """Load and display a specific workflow."""
    try:
        # Mock workflow loading
        workflows_data = _get_mock_workflows()
        workflow = next((w for w in workflows_data if w["name"] == name), None)
        
        if not workflow:
            console.print(f"❌ [red]Workflow '{name}' not found[/red]")
            console.print("💡 [blue]List available workflows with: python main.py workflow list[/blue]")
            return
        
        # Display workflow details
        console.print(Panel(
            f"**Name:** {workflow['name']}\n"
            f"**Type:** {workflow['type']}\n"
            f"**Steps:** {workflow['steps']}\n"
            f"**Created:** {workflow['created']}\n"
            f"**Status:** {workflow['status']}\n"
            f"**Description:** {workflow.get('description', 'No description available')}",
            title="Workflow Details",
            border_style="cyan"
        ))
        
        # Show workflow steps
        console.print("\n📋 [bold cyan]Workflow Steps:[/bold cyan]")
        for i, step in enumerate(workflow.get("step_details", []), 1):
            console.print(f"  {i}. {step}")
        
        console.print(f"\n💡 [blue]Run this workflow with: python main.py workflow run --name '{name}'[/blue]")
        
    except Exception as e:
        console.print(f"❌ [red]Failed to load workflow: {e}[/red]")
        logger.exception("Failed to load workflow")


def _run_workflow(name: str):
    """Execute a specific workflow."""
    try:
        # Mock workflow execution
        workflows_data = _get_mock_workflows()
        workflow = next((w for w in workflows_data if w["name"] == name), None)
        
        if not workflow:
            console.print(f"❌ [red]Workflow '{name}' not found[/red]")
            console.print("💡 [blue]List available workflows with: python main.py workflow list[/blue]")
            return
        
        console.print(f"🚀 [bold green]Executing workflow: {workflow['name']}[/bold green]")
        console.print(f"📋 Type: {workflow['type']}")
        console.print(f"📝 Steps: {workflow['steps']}")
        
        # Simulate workflow execution with progress
        with EnhancedProgress() as progress:
            task = progress.add_task(
                f"Executing {workflow['name']}",
                total=workflow['steps']
            )
            
            import time
            for i, step in enumerate(workflow.get("step_details", []), 1):
                console.print(f"  📍 Step {i}: {step}")
                time.sleep(0.5)  # Simulate work
                progress.update(task, advance=1)
        
        console.print(f"\n✅ [bold green]Workflow '{name}' completed successfully![/bold green]")
        console.print("📊 [blue]Results would be displayed here in a real implementation[/blue]")
        
    except Exception as e:
        console.print(f"❌ [red]Failed to run workflow: {e}[/red]")
        logger.exception("Failed to run workflow")


def _get_mock_workflows() -> List[Dict[str, Any]]:
    """Get mock workflow data for demonstration."""
    return [
        {
            "name": "Daily Analysis",
            "type": "daily_update",
            "steps": 4,
            "created": "2024-01-15",
            "status": "ready",
            "description": "Daily market data analysis workflow",
            "step_details": [
                "Fetch daily OHLCV data for SP500 symbols",
                "Calculate technical indicators",
                "Generate analysis reports",
                "Send notifications"
            ]
        },
        {
            "name": "Historical Backfill",
            "type": "backfill",
            "steps": 3,
            "created": "2024-01-10",
            "status": "ready",
            "description": "Historical data backfill for research",
            "step_details": [
                "Identify missing data gaps",
                "Fetch historical data from API",
                "Validate and store data"
            ]
        },
        {
            "name": "Multi-Symbol Analysis",
            "type": "multi_symbol",
            "steps": 5,
            "created": "2024-01-08",
            "status": "ready",
            "description": "Cross-symbol correlation analysis",
            "step_details": [
                "Load symbol groups",
                "Fetch synchronized data",
                "Calculate correlations",
                "Generate visualization",
                "Export results"
            ]
        }
    ]


# Export the app for module imports
__all__ = ["app", "workflows", "workflow"]