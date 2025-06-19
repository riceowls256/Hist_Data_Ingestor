"""
Base classes and decorators for CLI commands.
"""

import functools
from typing import Any, Callable, Dict, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..common.utils import get_logger

console = Console()
logger = get_logger(__name__)


class BaseCommand:
    """Base class for all CLI commands providing common functionality."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.console = console
        self.logger = logger
    
    def log_start(self, operation: str) -> None:
        """Log the start of a command operation."""
        self.logger.info(f"Starting {operation}", command=self.name)
    
    def log_success(self, operation: str, **kwargs) -> None:
        """Log successful completion of a command operation."""
        self.logger.info(f"Completed {operation}", command=self.name, **kwargs)
    
    def log_error(self, operation: str, error: Exception, **kwargs) -> None:
        """Log error during command operation."""
        self.logger.error(f"Failed {operation}: {error}", command=self.name, error=str(error), **kwargs)


def command_with_progress(operation_name: str = "Operation"):
    """Decorator to add progress tracking to CLI commands."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"{operation_name}...", total=None)
                try:
                    result = func(*args, **kwargs)
                    progress.update(task, description=f"{operation_name} completed ✓")
                    return result
                except Exception as e:
                    progress.update(task, description=f"{operation_name} failed ✗")
                    raise e
        return wrapper
    return decorator


def command_with_validation(validate_func: Optional[Callable] = None):
    """Decorator to add input validation to CLI commands."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if validate_func:
                validation_result = validate_func(**kwargs)
                if not validation_result:
                    raise ValueError("Command validation failed")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def handle_common_errors(func: Callable) -> Callable:
    """Decorator to handle common CLI errors gracefully."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled by user[/yellow]")
            raise typer.Exit(1)
        except Exception as e:
            logger.error(f"Command failed: {e}", command=func.__name__, error=str(e))
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    return wrapper