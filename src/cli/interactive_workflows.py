"""
Interactive workflow builder for creating complex operations step-by-step.

Provides guided workflow creation, parameter templates, workflow persistence,
and batch operation planning with intelligent validation and suggestions.
"""

import json
import uuid
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime, date, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import copy

from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn

from .smart_validation import SmartValidator, ValidationResult, ValidationLevel
from src.utils.custom_logger import get_logger

console = Console()
logger = get_logger(__name__)


class WorkflowType(Enum):
    """Types of workflows available."""
    BACKFILL = "backfill"
    DAILY_UPDATE = "daily_update"
    MULTI_SYMBOL = "multi_symbol"
    DATA_QUALITY = "data_quality"
    CUSTOM = "custom"


class StepStatus(Enum):
    """Status of workflow steps."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class WorkflowStep:
    """Individual step in a workflow."""
    id: str
    name: str
    description: str
    step_type: str
    parameters: Dict[str, Any]
    status: StepStatus = StepStatus.PENDING
    validation_results: List[ValidationResult] = None
    execution_time: Optional[float] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.validation_results is None:
            self.validation_results = []


@dataclass
class WorkflowTemplate:
    """Template for creating workflows."""
    id: str
    name: str
    description: str
    workflow_type: WorkflowType
    default_parameters: Dict[str, Any]
    steps: List[Dict[str, Any]]
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class Workflow:
    """Complete workflow definition."""
    id: str
    name: str
    description: str
    workflow_type: WorkflowType
    steps: List[WorkflowStep]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class WorkflowBuilder:
    """Interactive workflow builder for complex operations."""
    
    def __init__(self, validator: Optional[SmartValidator] = None,
                 templates_dir: Optional[Path] = None,
                 workflows_dir: Optional[Path] = None):
        """Initialize workflow builder.
        
        Args:
            validator: SmartValidator instance for input validation
            templates_dir: Directory for workflow templates
            workflows_dir: Directory for saved workflows
        """
        logger.info("workflow_builder_init_started", 
                    templates_dir=str(templates_dir) if templates_dir else None,
                    workflows_dir=str(workflows_dir) if workflows_dir else None)
        
        self.validator = validator or SmartValidator()
        self.templates_dir = templates_dir or Path.home() / ".hdi_workflow_templates"
        self.workflows_dir = workflows_dir or Path.home() / ".hdi_workflows"
        
        # Ensure directories exist
        self.templates_dir.mkdir(exist_ok=True)
        self.workflows_dir.mkdir(exist_ok=True)
        logger.debug("workflow_directories_created", 
                     templates_dir=str(self.templates_dir),
                     workflows_dir=str(self.workflows_dir))
        
        # Load built-in templates
        self.templates = self._load_builtin_templates()
        logger.debug("builtin_templates_loaded", template_count=len(self.templates))
        
        # Load custom templates
        self._load_custom_templates()
        
        logger.info("workflow_builder_init_completed", 
                    total_templates=len(self.templates),
                    templates_dir=str(self.templates_dir),
                    workflows_dir=str(self.workflows_dir))
        
    def build_workflow(self, workflow_type: Optional[WorkflowType] = None) -> Optional[Workflow]:
        """Build a workflow interactively.
        
        Args:
            workflow_type: Optional workflow type to start with
            
        Returns:
            Created workflow or None if cancelled
        """
        logger.info("workflow_build_started", workflow_type=workflow_type.value if workflow_type else None)
        console.print("\n🔧 [bold cyan]Interactive Workflow Builder[/bold cyan]\n")
        
        try:
            # Step 1: Choose workflow type
            if workflow_type is None:
                workflow_type = self._select_workflow_type()
                if workflow_type is None:
                    logger.info("workflow_build_cancelled", step="type_selection")
                    return None
                logger.debug("workflow_type_selected", workflow_type=workflow_type.value)
                    
            # Step 2: Choose template or start from scratch
            template = self._select_template(workflow_type)
            logger.debug("template_selected", 
                         template_name=template.name if template else "custom",
                         template_id=template.id if template else None)
            
            # Step 3: Configure workflow
            workflow = self._configure_workflow(workflow_type, template)
            if workflow is None:
                logger.info("workflow_build_cancelled", step="configuration")
                return None
            logger.debug("workflow_configured", 
                         workflow_name=workflow.name,
                         step_count=len(workflow.steps))
                
            # Step 4: Review and confirm
            if self._review_workflow(workflow):
                # Step 5: Save workflow option
                if Confirm.ask("\nSave this workflow for future use?", default=True):
                    workflow_name = Prompt.ask("Workflow name", default=workflow.name)
                    workflow.name = workflow_name
                    self._save_workflow(workflow)
                    console.print(f"✅ Workflow saved as '{workflow_name}'")
                    logger.info("workflow_saved", workflow_name=workflow_name, workflow_id=workflow.id)
                
                logger.info("workflow_build_completed", 
                            workflow_name=workflow.name,
                            workflow_type=workflow.workflow_type.value,
                            step_count=len(workflow.steps),
                            saved=True)
                return workflow
            else:
                console.print("❌ Workflow creation cancelled")
                logger.info("workflow_build_cancelled", step="review")
                return None
                
        except (KeyboardInterrupt, EOFError):
            console.print("\n⏹️  Workflow creation cancelled by user")
            logger.info("workflow_build_cancelled", reason="user_interrupt")
            return None
            
    def _select_workflow_type(self) -> Optional[WorkflowType]:
        """Select the workflow type interactively.
        
        Returns:
            Selected workflow type or None if cancelled
        """
        logger.debug("workflow_type_selection_started")
        
        options = [
            ("1", "Full Historical Backfill", WorkflowType.BACKFILL, 
             "Comprehensive historical data ingestion for multiple symbols"),
            ("2", "Daily Update Pipeline", WorkflowType.DAILY_UPDATE,
             "Automated daily data updates for existing datasets"),
            ("3", "Multi-Symbol Analysis", WorkflowType.MULTI_SYMBOL,
             "Parallel processing of multiple symbols with custom parameters"),
            ("4", "Data Quality Check", WorkflowType.DATA_QUALITY,
             "Validation and quality assessment of existing data"),
            ("5", "Custom Workflow", WorkflowType.CUSTOM,
             "Build a custom workflow from scratch")
        ]
        
        console.print("[cyan]Available Workflow Types:[/cyan]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Option", style="cyan", width=8)
        table.add_column("Type", style="green")
        table.add_column("Description", style="dim")
        
        for option, name, _, description in options:
            table.add_row(option, name, description)
            
        console.print(table)
        
        try:
            choice = IntPrompt.ask(
                "\nSelect workflow type",
                choices=["1", "2", "3", "4", "5"],
                default=1
            )
            selected_type = options[choice - 1][2]
            logger.debug("workflow_type_selection_completed", 
                         choice=choice, 
                         selected_type=selected_type.value)
            return selected_type
        except (KeyboardInterrupt, EOFError):
            logger.debug("workflow_type_selection_cancelled")
            return None
            
    def _select_template(self, workflow_type: WorkflowType) -> Optional[WorkflowTemplate]:
        """Select a template for the workflow type.
        
        Args:
            workflow_type: Workflow type to get templates for
            
        Returns:
            Selected template or None for custom
        """
        logger.debug("template_selection_started", workflow_type=workflow_type.value)
        
        # Filter templates by type
        available_templates = [t for t in self.templates if t.workflow_type == workflow_type]
        logger.debug("templates_filtered", 
                     workflow_type=workflow_type.value,
                     available_count=len(available_templates))
        
        if not available_templates:
            console.print(f"ℹ️  No templates available for {workflow_type.value}. Starting from scratch.")
            return None
            
        console.print(f"\n📋 [cyan]Available templates for {workflow_type.value}:[/cyan]\n")
        
        # Show template options
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Option", style="cyan", width=8)
        table.add_column("Template", style="green")
        table.add_column("Description", style="dim")
        
        for i, template in enumerate(available_templates, 1):
            table.add_row(str(i), template.name, template.description)
            
        table.add_row("0", "Custom", "Start from scratch without a template")
        
        console.print(table)
        
        try:
            choice = IntPrompt.ask(
                "Select template",
                choices=[str(i) for i in range(len(available_templates) + 1)],
                default=0
            )
            
            if choice == 0:
                logger.debug("template_selection_completed", selected="custom")
                return None
            else:
                selected_template = available_templates[choice - 1]
                logger.debug("template_selection_completed", 
                             selected_template=selected_template.name,
                             template_id=selected_template.id)
                return selected_template
                
        except (KeyboardInterrupt, EOFError):
            logger.debug("template_selection_cancelled")
            return None
            
    def _configure_workflow(self, workflow_type: WorkflowType, 
                          template: Optional[WorkflowTemplate]) -> Optional[Workflow]:
        """Configure workflow parameters and steps.
        
        Args:
            workflow_type: Type of workflow
            template: Optional template to base on
            
        Returns:
            Configured workflow or None if cancelled
        """
        logger.info("workflow_configuration_started", 
                    workflow_type=workflow_type.value,
                    using_template=template.name if template else None)
        
        console.print(f"\n⚙️  [cyan]Configuring {workflow_type.value} workflow[/cyan]\n")
        
        # Basic workflow info
        default_name = f"{workflow_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        workflow_name = Prompt.ask("Workflow name", default=default_name)
        
        workflow_description = Prompt.ask(
            "Description", 
            default=f"Interactive {workflow_type.value} workflow"
        )
        
        # Create workflow
        workflow_id = str(uuid.uuid4())
        workflow = Workflow(
            id=workflow_id,
            name=workflow_name,
            description=workflow_description,
            workflow_type=workflow_type,
            steps=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        logger.debug("workflow_object_created", 
                     workflow_id=workflow_id,
                     workflow_name=workflow_name,
                     workflow_type=workflow_type.value)
        
        # Configure based on type
        logger.debug("workflow_type_specific_configuration_started", workflow_type=workflow_type.value)
        
        if workflow_type == WorkflowType.BACKFILL:
            result = self._configure_backfill_workflow(workflow, template)
        elif workflow_type == WorkflowType.DAILY_UPDATE:
            result = self._configure_daily_update_workflow(workflow, template)
        elif workflow_type == WorkflowType.MULTI_SYMBOL:
            result = self._configure_multi_symbol_workflow(workflow, template)
        elif workflow_type == WorkflowType.DATA_QUALITY:
            result = self._configure_data_quality_workflow(workflow, template)
        else:  # CUSTOM
            result = self._configure_custom_workflow(workflow, template)
            
        if result:
            logger.info("workflow_configuration_completed", 
                        workflow_type=workflow_type.value,
                        step_count=len(result.steps),
                        workflow_name=result.name)
        else:
            logger.info("workflow_configuration_cancelled", workflow_type=workflow_type.value)
            
        return result
            
    def _configure_backfill_workflow(self, workflow: Workflow, 
                                   template: Optional[WorkflowTemplate]) -> Optional[Workflow]:
        """Configure a backfill workflow.
        
        Args:
            workflow: Base workflow to configure
            template: Optional template
            
        Returns:
            Configured workflow or None if cancelled
        """
        logger.info("backfill_workflow_configuration_started", workflow_id=workflow.id)
        console.print("📈 [green]Configuring Historical Backfill[/green]")
        
        # Symbol selection with validation
        symbols_input = Prompt.ask(
            "\nSymbol list (comma-separated)",
            default="ES.c.0,NQ.c.0,CL.c.0"
        )
        
        symbol_validation = self.validator.validate_symbol_list(symbols_input, interactive=True)
        self.validator.show_validation_result(symbol_validation, "Symbol Validation")
        
        logger.debug("symbol_validation_completed", 
                     symbols_input=symbols_input,
                     is_valid=symbol_validation.is_valid)
        
        if not symbol_validation.is_valid and not Confirm.ask("Continue with invalid symbols?"):
            logger.info("backfill_workflow_configuration_cancelled", reason="invalid_symbols")
            return None
            
        # Date range selection with market calendar
        console.print("\n📅 [green]Date Range Configuration[/green]")
        
        # Suggest intelligent defaults
        end_date = date.today() - timedelta(days=1)  # Yesterday
        start_date = end_date - timedelta(days=365)  # 1 year ago
        
        start_date_str = Prompt.ask("Start date (YYYY-MM-DD)", default=str(start_date))
        end_date_str = Prompt.ask("End date (YYYY-MM-DD)", default=str(end_date))
        
        date_validation = self.validator.validate_date_range(
            start_date_str, end_date_str, interactive=True
        )
        self.validator.show_validation_result(date_validation, "Date Range Validation")
        
        logger.debug("date_validation_completed", 
                     start_date=start_date_str,
                     end_date=end_date_str,
                     is_valid=date_validation.is_valid)
        
        if not date_validation.is_valid and not Confirm.ask("Continue with invalid dates?"):
            logger.info("backfill_workflow_configuration_cancelled", reason="invalid_dates")
            return None
            
        # Schema selection
        console.print("\n📊 [green]Data Schema Selection[/green]")
        schema_input = Prompt.ask("Schema", default="ohlcv-1d")
        
        schema_validation = self.validator.validate_schema(schema_input)
        self.validator.show_validation_result(schema_validation, "Schema Validation")
        
        # Processing options
        console.print("\n⚙️  [green]Processing Options[/green]")
        batch_size = IntPrompt.ask("Batch size (symbols processed in parallel)", default=5)
        retry_failed = Confirm.ask("Automatically retry failed operations?", default=True)
        
        # Create workflow steps
        steps = [
            WorkflowStep(
                id="validate_inputs",
                name="Validate Inputs",
                description="Validate symbols, dates, and configuration",
                step_type="validation",
                parameters={
                    "symbols": symbols_input,
                    "start_date": start_date_str,
                    "end_date": end_date_str,
                    "schema": schema_input
                }
            ),
            WorkflowStep(
                id="prepare_batches",
                name="Prepare Batches",
                description=f"Organize {len(symbols_input.split(','))} symbols into batches of {batch_size}",
                step_type="preparation",
                parameters={
                    "batch_size": batch_size,
                    "symbols": symbols_input.split(',')
                }
            ),
            WorkflowStep(
                id="execute_ingestion",
                name="Execute Ingestion",
                description="Process all symbol batches with progress tracking",
                step_type="ingestion",
                parameters={
                    "schema": schema_input,
                    "start_date": start_date_str,
                    "end_date": end_date_str,
                    "retry_failed": retry_failed
                }
            ),
            WorkflowStep(
                id="verify_results",
                name="Verify Results",
                description="Check ingestion results and generate summary",
                step_type="verification",
                parameters={
                    "expected_symbols": len(symbols_input.split(',')),
                    "generate_report": True
                }
            )
        ]
        
        workflow.steps = steps
        
        logger.info("backfill_workflow_configuration_completed", 
                    workflow_id=workflow.id,
                    symbol_count=len(symbols_input.split(',')),
                    batch_size=batch_size,
                    schema=schema_input,
                    date_range=f"{start_date_str} to {end_date_str}",
                    step_count=len(steps))
        
        return workflow
        
    def _configure_daily_update_workflow(self, workflow: Workflow,
                                       template: Optional[WorkflowTemplate]) -> Optional[Workflow]:
        """Configure a daily update workflow.
        
        Args:
            workflow: Base workflow to configure
            template: Optional template
            
        Returns:
            Configured workflow or None if cancelled
        """
        console.print("📅 [green]Configuring Daily Update Pipeline[/green]")
        
        # Symbol groups for daily updates
        symbol_group = Prompt.ask(
            "\nSymbol group for daily updates",
            default="SP500_SAMPLE"
        )
        
        # Schemas to update
        schemas = Prompt.ask(
            "Schemas to update (comma-separated)",
            default="ohlcv-1d,trades"
        ).split(',')
        
        # Update window
        lookback_days = IntPrompt.ask("Lookback days (for data refresh)", default=3)
        
        # Scheduling options
        console.print("\n⏰ [green]Scheduling Options[/green]")
        auto_schedule = Confirm.ask("Enable automatic scheduling?", default=False)
        
        schedule_time = None
        if auto_schedule:
            schedule_time = Prompt.ask("Daily execution time (HH:MM)", default="06:00")
            
        # Create workflow steps
        steps = [
            WorkflowStep(
                id="check_market_status",
                name="Check Market Status",
                description="Verify if market was open and data is available",
                step_type="validation",
                parameters={
                    "check_market_calendar": True,
                    "lookback_days": lookback_days
                }
            ),
            WorkflowStep(
                id="resolve_symbols",
                name="Resolve Symbol Group",
                description=f"Get current symbol list for {symbol_group}",
                step_type="preparation",
                parameters={
                    "symbol_group": symbol_group,
                    "update_cache": True
                }
            ),
            WorkflowStep(
                id="incremental_update",
                name="Incremental Data Update",
                description=f"Update last {lookback_days} days for all schemas",
                step_type="ingestion",
                parameters={
                    "schemas": schemas,
                    "lookback_days": lookback_days,
                    "overwrite_existing": True
                }
            ),
            WorkflowStep(
                id="quality_check",
                name="Data Quality Check",
                description="Validate updated data and check for gaps",
                step_type="verification",
                parameters={
                    "check_gaps": True,
                    "alert_on_issues": True
                }
            )
        ]
        
        if auto_schedule:
            steps.append(WorkflowStep(
                id="schedule_next",
                name="Schedule Next Run",
                description=f"Schedule next execution for {schedule_time}",
                step_type="scheduling",
                parameters={
                    "schedule_time": schedule_time,
                    "repeat": "daily"
                }
            ))
            
        workflow.steps = steps
        workflow.metadata["auto_schedule"] = auto_schedule
        workflow.metadata["schedule_time"] = schedule_time
        
        return workflow
        
    def _configure_multi_symbol_workflow(self, workflow: Workflow,
                                       template: Optional[WorkflowTemplate]) -> Optional[Workflow]:
        """Configure a multi-symbol analysis workflow.
        
        Args:
            workflow: Base workflow to configure
            template: Optional template
            
        Returns:
            Configured workflow or None if cancelled
        """
        console.print("🎯 [green]Configuring Multi-Symbol Analysis[/green]")
        
        # Symbol configuration with different parameters per symbol
        symbols_config = []
        
        console.print("\n📋 [cyan]Symbol-specific Configuration[/cyan]")
        console.print("Configure each symbol separately (empty symbol to finish):\n")
        
        while True:
            symbol = Prompt.ask("Symbol (or press Enter to finish)", default="")
            if not symbol:
                break
                
            symbol_validation = self.validator.validate_symbol(symbol, interactive=True)
            if not symbol_validation.is_valid:
                if not Confirm.ask("Add anyway?"):
                    continue
                    
            # Symbol-specific parameters
            schema = Prompt.ask(f"Schema for {symbol}", default="ohlcv-1d")
            
            # Custom date range option
            use_custom_dates = Confirm.ask(f"Custom date range for {symbol}?", default=False)
            if use_custom_dates:
                start_date = Prompt.ask("Start date", default="2024-01-01")
                end_date = Prompt.ask("End date", default="2024-12-31")
            else:
                start_date = end_date = None
                
            symbols_config.append({
                "symbol": symbol,
                "schema": schema,
                "start_date": start_date,
                "end_date": end_date
            })
            
            console.print(f"✅ Added {symbol} configuration\n")
            
        if not symbols_config:
            console.print("❌ No symbols configured")
            return None
            
        # Processing strategy
        console.print("\n⚙️  [green]Processing Strategy[/green]")
        parallel_processing = Confirm.ask("Enable parallel processing?", default=True)
        
        if parallel_processing:
            max_concurrent = IntPrompt.ask("Maximum concurrent operations", default=3)
        else:
            max_concurrent = 1
            
        # Analysis options
        generate_comparison = Confirm.ask("Generate comparison analysis?", default=True)
        export_results = Confirm.ask("Export results to files?", default=True)
        
        # Create workflow steps
        steps = [
            WorkflowStep(
                id="validate_configurations",
                name="Validate Symbol Configurations",
                description=f"Validate configuration for {len(symbols_config)} symbols",
                step_type="validation",
                parameters={
                    "symbols_config": symbols_config,
                    "validate_dates": True,
                    "validate_schemas": True
                }
            ),
            WorkflowStep(
                id="process_symbols",
                name="Process Symbols",
                description="Execute data ingestion for all configured symbols",
                step_type="ingestion",
                parameters={
                    "symbols_config": symbols_config,
                    "parallel": parallel_processing,
                    "max_concurrent": max_concurrent
                }
            )
        ]
        
        if generate_comparison:
            steps.append(WorkflowStep(
                id="generate_analysis",
                name="Generate Comparison Analysis",
                description="Create cross-symbol analysis and statistics",
                step_type="analysis",
                parameters={
                    "comparison_metrics": ["volume", "volatility", "returns"],
                    "generate_charts": True
                }
            ))
            
        if export_results:
            steps.append(WorkflowStep(
                id="export_results",
                name="Export Results",
                description="Export data and analysis to various formats",
                step_type="export",
                parameters={
                    "formats": ["csv", "json", "parquet"],
                    "include_metadata": True
                }
            ))
            
        workflow.steps = steps
        workflow.metadata["symbols_count"] = len(symbols_config)
        workflow.metadata["parallel_processing"] = parallel_processing
        
        return workflow
        
    def _configure_data_quality_workflow(self, workflow: Workflow,
                                       template: Optional[WorkflowTemplate]) -> Optional[Workflow]:
        """Configure a data quality check workflow.
        
        Args:
            workflow: Base workflow to configure  
            template: Optional template
            
        Returns:
            Configured workflow or None if cancelled
        """
        console.print("🔍 [green]Configuring Data Quality Check[/green]")
        
        # Scope definition
        console.print("\n📊 [cyan]Quality Check Scope[/cyan]")
        
        check_scope = Prompt.ask(
            "Check scope",
            choices=["all", "recent", "symbol_list", "date_range"],
            default="recent"
        )
        
        if check_scope == "symbol_list":
            symbols_input = Prompt.ask("Symbol list (comma-separated)")
            scope_params = {"symbols": symbols_input.split(',')}
        elif check_scope == "date_range":
            start_date = Prompt.ask("Start date", default="2024-01-01")
            end_date = Prompt.ask("End date", default="2024-12-31")
            scope_params = {"start_date": start_date, "end_date": end_date}
        elif check_scope == "recent":
            days_back = IntPrompt.ask("Days to check back", default=30)
            scope_params = {"days_back": days_back}
        else:  # all
            scope_params = {}
            
        # Quality checks to perform
        console.print("\n✅ [cyan]Quality Checks[/cyan]")
        
        quality_checks = {
            "missing_data": Confirm.ask("Check for missing data/gaps?", default=True),
            "duplicate_records": Confirm.ask("Check for duplicate records?", default=True),
            "data_consistency": Confirm.ask("Check data consistency?", default=True),
            "outlier_detection": Confirm.ask("Detect outliers?", default=True),
            "schema_validation": Confirm.ask("Validate against schema?", default=True),
            "referential_integrity": Confirm.ask("Check referential integrity?", default=False)
        }
        
        # Reporting options
        console.print("\n📋 [cyan]Reporting Options[/cyan]")
        
        generate_detailed_report = Confirm.ask("Generate detailed report?", default=True)
        alert_on_issues = Confirm.ask("Alert on quality issues?", default=True)
        
        if alert_on_issues:
            alert_threshold = Prompt.ask(
                "Alert threshold",
                choices=["any", "warning", "error"],
                default="warning"
            )
        else:
            alert_threshold = None
            
        # Create workflow steps
        steps = [
            WorkflowStep(
                id="scan_data",
                name="Scan Data Sources",
                description="Identify data to be checked based on scope",
                step_type="scanning",
                parameters={
                    "scope": check_scope,
                    "scope_params": scope_params
                }
            ),
            WorkflowStep(
                id="run_quality_checks",
                name="Run Quality Checks",
                description="Execute all enabled quality checks",
                step_type="quality_check",
                parameters={
                    "checks": quality_checks,
                    "parallel_execution": True
                }
            ),
            WorkflowStep(
                id="analyze_results",
                name="Analyze Results",
                description="Analyze quality check results and identify issues",
                step_type="analysis",
                parameters={
                    "categorize_issues": True,
                    "calculate_scores": True
                }
            )
        ]
        
        if generate_detailed_report:
            steps.append(WorkflowStep(
                id="generate_report",
                name="Generate Quality Report",
                description="Create comprehensive data quality report",
                step_type="reporting",
                parameters={
                    "include_charts": True,
                    "export_formats": ["html", "pdf", "json"]
                }
            ))
            
        if alert_on_issues:
            steps.append(WorkflowStep(
                id="send_alerts",
                name="Send Quality Alerts",
                description="Send alerts for identified quality issues",
                step_type="alerting",
                parameters={
                    "threshold": alert_threshold,
                    "notification_methods": ["console", "log"]
                }
            ))
            
        workflow.steps = steps
        workflow.metadata["check_scope"] = check_scope
        workflow.metadata["quality_checks"] = quality_checks
        
        return workflow
        
    def _configure_custom_workflow(self, workflow: Workflow,
                                 template: Optional[WorkflowTemplate]) -> Optional[Workflow]:
        """Configure a custom workflow from scratch.
        
        Args:
            workflow: Base workflow to configure
            template: Optional template
            
        Returns:
            Configured workflow or None if cancelled
        """
        console.print("🛠️  [green]Building Custom Workflow[/green]")
        
        console.print("\nAdd steps to your workflow (empty step name to finish):\n")
        
        steps = []
        step_counter = 1
        
        while True:
            step_name = Prompt.ask(f"Step {step_counter} name (or press Enter to finish)", default="")
            if not step_name:
                break
                
            step_description = Prompt.ask("Step description", default=f"Custom step {step_counter}")
            
            step_type = Prompt.ask(
                "Step type",
                choices=["validation", "preparation", "ingestion", "analysis", "export", "custom"],
                default="custom"
            )
            
            # Collect step parameters
            console.print(f"\n⚙️  Parameters for {step_name}:")
            parameters = {}
            
            while True:
                param_name = Prompt.ask("Parameter name (or press Enter to finish)", default="")
                if not param_name:
                    break
                    
                param_value = Prompt.ask(f"Value for {param_name}")
                
                # Try to parse as JSON for complex values
                try:
                    if param_value.startswith('{') or param_value.startswith('['):
                        param_value = json.loads(param_value)
                    elif param_value.lower() in ['true', 'false']:
                        param_value = param_value.lower() == 'true'
                    elif param_value.isdigit():
                        param_value = int(param_value)
                    elif '.' in param_value and param_value.replace('.', '').isdigit():
                        param_value = float(param_value)
                except:
                    # Keep as string if parsing fails
                    pass
                    
                parameters[param_name] = param_value
                
            step = WorkflowStep(
                id=f"step_{step_counter}",
                name=step_name,
                description=step_description,
                step_type=step_type,
                parameters=parameters
            )
            
            steps.append(step)
            console.print(f"✅ Added step: {step_name}\n")
            step_counter += 1
            
        if not steps:
            console.print("❌ No steps configured")
            return None
            
        workflow.steps = steps
        return workflow
        
    def _review_workflow(self, workflow: Workflow) -> bool:
        """Review workflow and confirm creation.
        
        Args:
            workflow: Workflow to review
            
        Returns:
            True if user confirms creation
        """
        console.print("\n📋 [bold cyan]Workflow Review[/bold cyan]\n")
        
        # Basic info
        info_table = Table(show_header=False, box=None)
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="green")
        
        info_table.add_row("Name", workflow.name)
        info_table.add_row("Type", workflow.workflow_type.value)
        info_table.add_row("Description", workflow.description)
        info_table.add_row("Steps", str(len(workflow.steps)))
        
        console.print(Panel(info_table, title="📝 Workflow Information", border_style="blue"))
        
        # Steps breakdown
        console.print("\n📋 [cyan]Workflow Steps:[/cyan]\n")
        
        steps_table = Table(show_header=True, header_style="bold magenta")
        steps_table.add_column("Step", style="cyan", width=3)
        steps_table.add_column("Name", style="green")
        steps_table.add_column("Type", style="yellow")
        steps_table.add_column("Description", style="dim")
        
        for i, step in enumerate(workflow.steps, 1):
            steps_table.add_row(
                str(i),
                step.name,
                step.step_type,
                step.description
            )
            
        console.print(steps_table)
        
        # Show parameters for each step if requested
        if Confirm.ask("\nShow detailed step parameters?", default=False):
            for i, step in enumerate(workflow.steps, 1):
                console.print(f"\n[cyan]Step {i}: {step.name}[/cyan]")
                if step.parameters:
                    params_text = json.dumps(step.parameters, indent=2)
                    console.print(Panel(params_text, border_style="dim"))
                else:
                    console.print("  [dim]No parameters[/dim]")
                    
        # Confirmation
        return Confirm.ask("\n✨ Create this workflow?", default=True)
        
    def _save_workflow(self, workflow: Workflow):
        """Save workflow to disk.
        
        Args:
            workflow: Workflow to save
        """
        logger.info("workflow_save_started", 
                    workflow_id=workflow.id,
                    workflow_name=workflow.name)
        
        workflow_file = self.workflows_dir / f"{workflow.id}.json"
        
        # Convert to serializable format
        workflow_data = {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "workflow_type": workflow.workflow_type.value,
            "steps": [
                {
                    "id": step.id,
                    "name": step.name,
                    "description": step.description,
                    "step_type": step.step_type,
                    "parameters": step.parameters,
                    "status": step.status.value
                }
                for step in workflow.steps
            ],
            "created_at": workflow.created_at.isoformat(),
            "updated_at": workflow.updated_at.isoformat(),
            "metadata": workflow.metadata
        }
        
        try:
            with open(workflow_file, 'w') as f:
                json.dump(workflow_data, f, indent=2)
            
            logger.info("workflow_save_completed", 
                        workflow_id=workflow.id,
                        workflow_name=workflow.name,
                        file_path=str(workflow_file))
        except Exception as e:
            console.print(f"❌ Failed to save workflow: {e}")
            logger.error("workflow_save_failed", 
                         workflow_id=workflow.id,
                         workflow_name=workflow.name,
                         error=str(e),
                         error_type=type(e).__name__)
            
    def load_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Load a saved workflow.
        
        Args:
            workflow_id: ID of workflow to load
            
        Returns:
            Loaded workflow or None if not found
        """
        logger.info("workflow_load_started", workflow_id=workflow_id)
        
        workflow_file = self.workflows_dir / f"{workflow_id}.json"
        
        if not workflow_file.exists():
            logger.warning("workflow_load_failed", 
                           workflow_id=workflow_id, 
                           reason="file_not_found",
                           file_path=str(workflow_file))
            return None
            
        try:
            with open(workflow_file, 'r') as f:
                data = json.load(f)
                
            # Convert back to objects
            steps = [
                WorkflowStep(
                    id=step_data["id"],
                    name=step_data["name"],
                    description=step_data["description"],
                    step_type=step_data["step_type"],
                    parameters=step_data["parameters"],
                    status=StepStatus(step_data["status"])
                )
                for step_data in data["steps"]
            ]
            
            workflow = Workflow(
                id=data["id"],
                name=data["name"],
                description=data["description"],
                workflow_type=WorkflowType(data["workflow_type"]),
                steps=steps,
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
                metadata=data.get("metadata", {})
            )
            
            logger.info("workflow_load_completed", 
                        workflow_id=workflow_id,
                        workflow_name=workflow.name,
                        step_count=len(workflow.steps))
            
            return workflow
            
        except Exception as e:
            console.print(f"❌ Failed to load workflow: {e}")
            logger.error("workflow_load_failed", 
                         workflow_id=workflow_id,
                         error=str(e),
                         error_type=type(e).__name__)
            return None
            
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all saved workflows.
        
        Returns:
            List of workflow summaries
        """
        logger.debug("workflow_list_started")
        workflows = []
        
        for workflow_file in self.workflows_dir.glob("*.json"):
            try:
                with open(workflow_file, 'r') as f:
                    data = json.load(f)
                    
                workflows.append({
                    "id": data["id"],
                    "name": data["name"],
                    "type": data["workflow_type"],
                    "steps": len(data["steps"]),
                    "created_at": data["created_at"],
                    "updated_at": data["updated_at"]
                })
            except:
                continue
                
        result = sorted(workflows, key=lambda x: x["created_at"], reverse=True)
        
        logger.debug("workflow_list_completed", workflow_count=len(result))
        return result
        
    def show_workflows(self):
        """Display all saved workflows in a table."""
        workflows = self.list_workflows()
        
        if not workflows:
            console.print("📭 No saved workflows found")
            return
            
        console.print(f"\n📋 [bold cyan]Saved Workflows ({len(workflows)})[/bold cyan]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="green")
        table.add_column("Type", style="cyan")
        table.add_column("Steps", style="yellow", justify="right")
        table.add_column("Created", style="dim")
        
        for workflow in workflows:
            created_date = datetime.fromisoformat(workflow["created_at"]).strftime("%Y-%m-%d %H:%M")
            table.add_row(
                workflow["name"],
                workflow["type"],
                str(workflow["steps"]),
                created_date
            )
            
        console.print(table)
        
    def _load_builtin_templates(self) -> List[WorkflowTemplate]:
        """Load built-in workflow templates.
        
        Returns:
            List of built-in templates
        """
        templates = []
        
        # Backfill template
        templates.append(WorkflowTemplate(
            id="backfill_standard",
            name="Standard Backfill",
            description="Standard historical data backfill with validation",
            workflow_type=WorkflowType.BACKFILL,
            default_parameters={
                "batch_size": 5,
                "retry_failed": True,
                "schema": "ohlcv-1d"
            },
            steps=[
                {"name": "Validate Inputs", "type": "validation"},
                {"name": "Prepare Batches", "type": "preparation"},
                {"name": "Execute Ingestion", "type": "ingestion"},
                {"name": "Verify Results", "type": "verification"}
            ],
            tags=["standard", "backfill", "historical"]
        ))
        
        # Daily update template
        templates.append(WorkflowTemplate(
            id="daily_standard",
            name="Standard Daily Update",
            description="Standard daily data update pipeline",
            workflow_type=WorkflowType.DAILY_UPDATE,
            default_parameters={
                "lookback_days": 3,
                "schemas": ["ohlcv-1d"],
                "symbol_group": "SP500_SAMPLE"
            },
            steps=[
                {"name": "Check Market Status", "type": "validation"},
                {"name": "Resolve Symbols", "type": "preparation"},
                {"name": "Incremental Update", "type": "ingestion"},
                {"name": "Quality Check", "type": "verification"}
            ],
            tags=["daily", "update", "automation"]
        ))
        
        logger.debug("builtin_templates_loading_completed", template_count=len(templates))
        return templates
        
    def _load_custom_templates(self):
        """Load custom templates from disk."""
        logger.debug("custom_templates_loading_started")
        templates_file = self.templates_dir / "custom_templates.json"
        
        if not templates_file.exists():
            logger.debug("custom_templates_file_not_found", file_path=str(templates_file))
            return
            
        try:
            with open(templates_file, 'r') as f:
                custom_templates_data = json.load(f)
                
            for template_data in custom_templates_data:
                template = WorkflowTemplate(
                    id=template_data["id"],
                    name=template_data["name"],
                    description=template_data["description"],
                    workflow_type=WorkflowType(template_data["workflow_type"]),
                    default_parameters=template_data["default_parameters"],
                    steps=template_data["steps"],
                    tags=template_data.get("tags", [])
                )
                self.templates.append(template)
                
        except Exception:
            # If loading fails, just continue without custom templates
            pass


def create_interactive_workflow() -> Optional[Workflow]:
    """Create a workflow interactively.
    
    Returns:
        Created workflow or None if cancelled
    """
    logger.info("interactive_workflow_creation_started")
    builder = WorkflowBuilder()
    result = builder.build_workflow()
    
    if result:
        logger.info("interactive_workflow_creation_completed", 
                    workflow_name=result.name,
                    workflow_id=result.id)
    else:
        logger.info("interactive_workflow_creation_cancelled")
    
    return result


def list_saved_workflows():
    """List all saved workflows."""
    logger.info("list_saved_workflows_called")
    builder = WorkflowBuilder()
    builder.show_workflows()


def load_workflow_by_name(name: str) -> Optional[Workflow]:
    """Load a workflow by name.
    
    Args:
        name: Name of workflow to load
        
    Returns:
        Loaded workflow or None if not found
    """
    builder = WorkflowBuilder()
    workflows = builder.list_workflows()
    
    for workflow_data in workflows:
        if workflow_data["name"] == name:
            return builder.load_workflow(workflow_data["id"])
            
    return None