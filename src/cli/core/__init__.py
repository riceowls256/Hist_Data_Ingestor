"""
CLI Core Package

This package contains shared CLI infrastructure including base classes,
common decorators, and CLI-specific types.
"""

from .base import BaseCommand, command_with_progress, command_with_validation
from .types import CLIConfig, CommandResult

__all__ = [
    "BaseCommand",
    "command_with_progress", 
    "command_with_validation",
    "CLIConfig",
    "CommandResult"
]