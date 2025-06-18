"""
CLI module for the Historical Data Ingestor.

Provides command-line interface components including help utilities,
examples, and troubleshooting guidance.
"""

from .help_utils import (
    CLIExamples,
    CLITroubleshooter,
    CLITips,
    show_examples,
    show_tips,
    validate_date_range,
    validate_symbols,
    format_schema_help,
    suggest_date_range
)

from .enhanced_help_utils import (
    InteractiveHelpMenu,
    QuickstartWizard,
    WorkflowExamples,
    CheatSheet,
    SymbolHelper,
    GuidedMode
)

__all__ = [
    "CLIExamples",
    "CLITroubleshooter", 
    "CLITips",
    "show_examples",
    "show_tips",
    "validate_date_range",
    "validate_symbols",
    "format_schema_help",
    "suggest_date_range",
    "InteractiveHelpMenu",
    "QuickstartWizard",
    "WorkflowExamples",
    "CheatSheet",
    "SymbolHelper",
    "GuidedMode"
]