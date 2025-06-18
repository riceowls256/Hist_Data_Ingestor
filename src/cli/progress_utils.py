"""
Enhanced progress tracking utilities for the CLI.

Provides detailed progress bars, ETA calculations, and performance metrics
for long-running operations like data ingestion and queries.
"""

from typing import Optional, Dict, Any, List, Callable, Deque, Tuple
from datetime import datetime, timedelta
import time
from contextlib import contextmanager
from collections import deque
import json
from pathlib import Path
import psutil
import os
import threading
import queue

from rich.console import Console
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn, 
    TaskProgressColumn, TimeRemainingColumn, TimeElapsedColumn,
    ProgressColumn, Task
)
from rich.text import Text
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.columns import Columns

console = Console()

# Configuration integration - imported after console to avoid circular imports
def _get_config():
    """Get configuration manager lazily to avoid circular imports."""
    try:
        from .config_manager import get_config
        return get_config()
    except ImportError:
        # Fallback if config system is not available
        return None

def _get_config_setting(path: str, default=None):
    """Get configuration setting with fallback."""
    config = _get_config()
    if config:
        try:
            from .config_manager import get_setting
            return get_setting(path, default)
        except:
            pass
    return default


class AdaptiveETACalculator:
    """Calculate ETAs with adaptive learning from operation history.
    
    This class tracks historical performance data to provide more accurate
    ETA estimates that improve over time. It stores operation-specific
    timing data and adjusts predictions based on recent performance.
    """
    
    def __init__(self, window_size: int = 100, history_file: Optional[Path] = None):
        """Initialize the adaptive ETA calculator.
        
        Args:
            window_size: Number of recent operations to keep in memory
            history_file: Optional file to persist timing data across sessions
        """
        self.window_size = window_size
        self.history_file = history_file or Path.home() / ".hdi_eta_history.json"
        self.throughput_history: Deque[float] = deque(maxlen=window_size)
        self.operation_times: Dict[str, Deque[Tuple[int, float]]] = {}
        self.current_operation_start: Optional[float] = None
        self.items_at_start: int = 0
        
        # Load historical data if available
        self._load_history()
        
    def _load_history(self) -> None:
        """Load historical timing data from disk."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    
                # Restore operation-specific history
                for op_type, timings in data.get('operation_times', {}).items():
                    self.operation_times[op_type] = deque(
                        [(t[0], t[1]) for t in timings[-50:]],  # Keep last 50
                        maxlen=50
                    )
                    
                # Restore general throughput history
                if 'throughput_history' in data:
                    self.throughput_history = deque(
                        data['throughput_history'][-self.window_size:],
                        maxlen=self.window_size
                    )
            except Exception:
                # If loading fails, start fresh
                pass
    
    def _save_history(self) -> None:
        """Save historical timing data to disk."""
        try:
            data = {
                'operation_times': {
                    op_type: list(timings)
                    for op_type, timings in self.operation_times.items()
                },
                'throughput_history': list(self.throughput_history),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            # Don't fail if we can't save history
            pass
    
    def start_operation(self, operation_type: str, items_completed: int = 0) -> None:
        """Mark the start of an operation.
        
        Args:
            operation_type: Type of operation (e.g., "databento_ohlcv_fetch")
            items_completed: Number of items already completed
        """
        self.current_operation_start = time.time()
        self.items_at_start = items_completed
        
    def update(self, operation_type: str, items_processed: int, time_taken: Optional[float] = None) -> None:
        """Update timing data with new observations.
        
        Args:
            operation_type: Type of operation
            items_processed: Total items processed so far
            time_taken: Time taken (seconds). If None, calculated from start_operation
        """
        if time_taken is None and self.current_operation_start:
            time_taken = time.time() - self.current_operation_start
            items_processed = items_processed - self.items_at_start
            
        if time_taken and time_taken > 0 and items_processed > 0:
            throughput = items_processed / time_taken
            self.throughput_history.append(throughput)
            
            # Store operation-specific timing
            if operation_type not in self.operation_times:
                self.operation_times[operation_type] = deque(maxlen=50)
            self.operation_times[operation_type].append((items_processed, time_taken))
            
            # Periodically save history
            if len(self.throughput_history) % 10 == 0:
                self._save_history()
    
    def estimate_remaining_time(self, operation_type: str, items_remaining: int, 
                              items_completed: int = 0, time_elapsed: float = 0) -> Optional[float]:
        """Estimate remaining time for an operation.
        
        Args:
            operation_type: Type of operation
            items_remaining: Number of items left to process
            items_completed: Items completed so far in current operation
            time_elapsed: Time elapsed in current operation
            
        Returns:
            Estimated seconds remaining, or None if no estimate available
        """
        # First, try to use current operation's throughput if we have enough data
        if items_completed > 10 and time_elapsed > 1:
            current_throughput = items_completed / time_elapsed
            
            # Blend with historical data if available
            if operation_type in self.operation_times and len(self.operation_times[operation_type]) > 2:
                # Get historical throughput for this operation type
                historical_throughputs = [
                    items / time_val for items, time_val in self.operation_times[operation_type]
                    if time_val > 0
                ]
                if historical_throughputs:
                    avg_historical = sum(historical_throughputs) / len(historical_throughputs)
                    # Weighted average: 70% current, 30% historical
                    blended_throughput = (0.7 * current_throughput + 0.3 * avg_historical)
                else:
                    blended_throughput = current_throughput
            else:
                blended_throughput = current_throughput
                
            if blended_throughput > 0:
                return items_remaining / blended_throughput
        
        # Fall back to operation-specific history
        if operation_type in self.operation_times and len(self.operation_times[operation_type]) > 2:
            recent_times = list(self.operation_times[operation_type])[-10:]
            avg_throughput = sum(items/time_val for items, time_val in recent_times) / len(recent_times)
            if avg_throughput > 0:
                return items_remaining / avg_throughput
        
        # Fall back to general throughput history
        if len(self.throughput_history) > 5:
            # Use median of recent throughputs for stability
            recent_throughputs = sorted(list(self.throughput_history)[-20:])
            median_throughput = recent_throughputs[len(recent_throughputs) // 2]
            if median_throughput > 0:
                return items_remaining / median_throughput
        
        return None
    
    def get_confidence_level(self, operation_type: str) -> str:
        """Get confidence level for ETA estimates.
        
        Args:
            operation_type: Type of operation
            
        Returns:
            Confidence level: "high", "medium", "low", or "none"
        """
        if operation_type in self.operation_times:
            sample_size = len(self.operation_times[operation_type])
            if sample_size >= 20:
                return "high"
            elif sample_size >= 5:
                return "medium"
            elif sample_size >= 1:
                return "low"
        elif len(self.throughput_history) >= 10:
            return "low"
        return "none"


class TransferSpeedColumn(ProgressColumn):
    """Show transfer speed for data operations."""
    
    def render(self, task: Task) -> Text:
        """Render transfer speed."""
        speed = task.fields.get('speed', 0)
        
        # Get colors from configuration
        success_color = _get_config_setting('colors.success', 'green')
        warning_color = _get_config_setting('colors.warning', 'yellow')
        error_color = _get_config_setting('colors.error', 'red')
        
        if speed > 0:
            if speed > 1_000_000:
                return Text(f"{speed/1_000_000:.1f} MB/s", style=f"bold {success_color}")
            elif speed > 1_000:
                return Text(f"{speed/1_000:.1f} KB/s", style=f"bold {warning_color}")
            else:
                return Text(f"{speed:.0f} B/s", style=f"bold {error_color}")
        return Text("-- B/s", style="dim")


class RecordCountColumn(ProgressColumn):
    """Show record count for data operations."""
    
    def render(self, task: Task) -> Text:
        """Render record count."""
        completed = int(task.completed)
        total = int(task.total) if task.total else 0
        
        # Get info color from configuration
        info_color = _get_config_setting('colors.info', 'cyan')
        
        if total > 0:
            return Text(f"{completed:,}/{total:,} records", style=info_color)
        else:
            return Text(f"{completed:,} records", style=info_color)


class ETAColumn(ProgressColumn):
    """Enhanced ETA column with better formatting."""
    
    def render(self, task: Task) -> Text:
        """Render ETA."""
        remaining = task.time_remaining
        if remaining is None:
            return Text("--:--", style="dim")
        
        # Get colors from configuration
        success_color = _get_config_setting('colors.success', 'green')
        warning_color = _get_config_setting('colors.warning', 'yellow')
        error_color = _get_config_setting('colors.error', 'red')
        
        if remaining < 60:
            return Text(f"{int(remaining)}s", style=f"bold {success_color}")
        elif remaining < 3600:
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            return Text(f"{mins}m {secs}s", style=f"bold {warning_color}")
        else:
            hours = int(remaining // 3600)
            mins = int((remaining % 3600) // 60)
            return Text(f"{hours}h {mins}m", style=f"bold {error_color}")


class AdaptiveETAColumn(ProgressColumn):
    """ETA column using adaptive learning for better predictions."""
    
    def __init__(self, calculator: Optional[AdaptiveETACalculator] = None):
        """Initialize adaptive ETA column.
        
        Args:
            calculator: Optional calculator instance to share across columns
        """
        super().__init__()
        self.calculator = calculator or AdaptiveETACalculator()
        self.last_update_time: Dict[int, float] = {}
        self.last_completed: Dict[int, int] = {}
        
    def render(self, task: Task) -> Text:
        """Render adaptive ETA."""
        task_id = id(task)
        current_time = time.time()
        
        # Get operation type from task fields
        operation_type = task.fields.get('operation_type', 'default')
        
        # Track progress
        if task_id not in self.last_update_time:
            self.last_update_time[task_id] = task.started
            self.last_completed[task_id] = 0
            self.calculator.start_operation(operation_type, 0)
        
        # Update calculator with progress
        if task.completed > self.last_completed.get(task_id, 0):
            items_delta = task.completed - self.last_completed[task_id]
            time_delta = current_time - self.last_update_time[task_id]
            
            if time_delta > 0.5:  # Update at most every 0.5 seconds
                self.calculator.update(operation_type, items_delta, time_delta)
                self.last_update_time[task_id] = current_time
                self.last_completed[task_id] = task.completed
        
        # Calculate ETA
        if task.total and task.completed < task.total:
            items_remaining = task.total - task.completed
            time_elapsed = current_time - task.started
            
            # Get adaptive estimate
            eta_seconds = self.calculator.estimate_remaining_time(
                operation_type, 
                items_remaining,
                task.completed,
                time_elapsed
            )
            
            if eta_seconds is not None:
                # Get confidence level for styling
                confidence = self.calculator.get_confidence_level(operation_type)
                
                # Get colors from configuration
                success_color = _get_config_setting('colors.success', 'green')
                warning_color = _get_config_setting('colors.warning', 'yellow')
                error_color = _get_config_setting('colors.error', 'red')
                
                # Format the ETA
                if eta_seconds < 60:
                    eta_text = f"{int(eta_seconds)}s"
                    style = f"bold {success_color}" if confidence == "high" else success_color
                elif eta_seconds < 3600:
                    mins = int(eta_seconds // 60)
                    secs = int(eta_seconds % 60)
                    eta_text = f"{mins}m {secs}s"
                    style = f"bold {warning_color}" if confidence == "high" else warning_color
                else:
                    hours = int(eta_seconds // 3600)
                    mins = int((eta_seconds % 3600) // 60)
                    eta_text = f"{hours}h {mins}m"
                    style = f"bold {error_color}" if confidence == "high" else error_color
                
                # Add confidence indicator if not high
                if confidence in ["medium", "low"]:
                    eta_text = f"~{eta_text}"
                elif confidence == "none":
                    eta_text = f"?{eta_text}"
                    
                return Text(eta_text, style=style)
        
        # Fall back to standard time remaining if available
        if hasattr(task, 'time_remaining') and task.time_remaining:
            remaining = task.time_remaining
            if remaining < 60:
                return Text(f"{int(remaining)}s", style="dim green")
            elif remaining < 3600:
                mins = int(remaining // 60)
                secs = int(remaining % 60)
                return Text(f"{mins}m {secs}s", style="dim yellow")
            else:
                hours = int(remaining // 3600)
                mins = int((remaining % 3600) // 60)
                return Text(f"{hours}h {mins}m", style="dim red")
        
        return Text("--:--", style="dim")


class EnhancedProgress:
    """Enhanced progress tracking with detailed metrics."""
    
    def __init__(self, description: str = "", show_speed: bool = None, 
                 show_eta: bool = None, show_records: bool = None,
                 use_adaptive_eta: bool = None, use_throttling: bool = None,
                 throttle_min_interval: float = None, throttle_max_interval: float = None):
        """Initialize enhanced progress tracker.
        
        Args:
            description: Initial description
            show_speed: Whether to show transfer speed (uses config if None)
            show_eta: Whether to show ETA (uses config if None)
            show_records: Whether to show record count (uses config if None)
            use_adaptive_eta: Whether to use adaptive ETA calculator (uses config if None)
            use_throttling: Whether to throttle high-frequency updates (uses config if None)
            throttle_min_interval: Minimum throttling interval (uses config if None)
            throttle_max_interval: Maximum throttling interval (uses config if None)
        """
        # Apply configuration defaults
        if show_speed is None:
            show_speed = _get_config_setting('progress.show_speed', True)
        if show_eta is None:
            show_eta = _get_config_setting('progress.show_eta', True)
        if show_records is None:
            show_records = _get_config_setting('progress.show_metrics', True)
        if use_adaptive_eta is None:
            use_adaptive_eta = _get_config_setting('progress.use_adaptive_eta', True)
        if use_throttling is None:
            use_throttling = _get_config_setting('progress.use_throttling', False)
        if throttle_min_interval is None:
            throttle_min_interval = 0.1
        if throttle_max_interval is None:
            throttle_max_interval = 0.5
        columns = [SpinnerColumn()]
        columns.append(TextColumn("[progress.description]{task.description}"))
        columns.append(BarColumn())
        columns.append(TaskProgressColumn())
        
        if show_records:
            columns.append(RecordCountColumn())
        if show_speed:
            columns.append(TransferSpeedColumn())
        if show_eta:
            if use_adaptive_eta:
                # Use shared calculator instance for all columns
                self.eta_calculator = AdaptiveETACalculator()
                columns.append(AdaptiveETAColumn(self.eta_calculator))
            else:
                columns.append(ETAColumn())
            
        columns.append(TimeElapsedColumn())
        
        self.progress = Progress(*columns, console=console)
        self.main_task = None
        self.sub_tasks = {}
        self.start_time = None
        self.description = description
        self.use_adaptive_eta = use_adaptive_eta
        self.use_throttling = use_throttling
        
        # Initialize throttler if requested
        self.throttler = None
        if use_throttling:
            self.throttler = ThrottledProgressUpdater(
                min_interval=throttle_min_interval,
                max_interval=throttle_max_interval,
                adaptive=True
            )
            self.throttler.set_target(self, "update_main")
        
    def __enter__(self):
        """Enter context manager."""
        self.progress.__enter__()
        self.start_time = time.time()
        self.main_task = self.progress.add_task(self.description, total=None)
        
        # Start throttler if enabled
        if self.throttler:
            self.throttler.start()
            
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        # Stop throttler first to flush any pending updates
        if self.throttler:
            self.throttler.stop()
            
        # Complete all tasks
        if self.main_task is not None:
            self.progress.update(self.main_task, completed=self.progress.tasks[self.main_task].total)
        for task_id in self.sub_tasks.values():
            task = self.progress.tasks[task_id]
            if task.total:
                self.progress.update(task_id, completed=task.total)
                
        self.progress.__exit__(exc_type, exc_val, exc_tb)
        
    def update_main(self, description: Optional[str] = None, 
                   total: Optional[int] = None, completed: Optional[int] = None,
                   advance: int = 0, operation_type: Optional[str] = None, **fields):
        """Update main task progress.
        
        Args:
            description: New description
            total: Total items
            completed: Completed items
            advance: Items to advance by
            operation_type: Type of operation for adaptive ETA
            **fields: Additional fields (e.g., speed)
        """
        update_kwargs = {}
        if description is not None:
            update_kwargs['description'] = description
        if total is not None:
            update_kwargs['total'] = total
        if completed is not None:
            update_kwargs['completed'] = completed
        if advance > 0:
            update_kwargs['advance'] = advance
            
        # Calculate speed if advancing
        if advance > 0 and self.start_time:
            elapsed = time.time() - self.start_time
            if elapsed > 0:
                current_task = self.progress.tasks[self.main_task]
                total_completed = (current_task.completed or 0) + advance
                fields['speed'] = total_completed / elapsed
                
        # Add operation type for adaptive ETA
        if operation_type and self.use_adaptive_eta:
            fields['operation_type'] = operation_type
        elif 'operation_type' not in fields and self.use_adaptive_eta:
            # Try to infer operation type from description
            desc_to_check = description or self.description
            if desc_to_check and 'databento' in desc_to_check.lower():
                if 'ohlcv' in desc_to_check.lower():
                    fields['operation_type'] = 'databento_ohlcv'
                elif 'trades' in desc_to_check.lower():
                    fields['operation_type'] = 'databento_trades'
                elif 'tbbo' in desc_to_check.lower():
                    fields['operation_type'] = 'databento_tbbo'
                else:
                    fields['operation_type'] = 'databento_generic'
            else:
                fields['operation_type'] = 'generic_ingestion'
                
        update_kwargs.update(fields)
        
        # Route through throttler if enabled, otherwise update directly
        if self.throttler and self.throttler.running:
            self.throttler.update("main", **update_kwargs)
        else:
            self.progress.update(self.main_task, **update_kwargs)
            
    def _direct_update_main(self, **kwargs):
        """Direct update bypassing throttler (used by throttler itself)."""
        if self.main_task is not None:
            self.progress.update(self.main_task, **kwargs)
        
    def add_subtask(self, name: str, description: str, total: Optional[int] = None) -> str:
        """Add a subtask.
        
        Args:
            name: Unique name for the subtask
            description: Task description
            total: Total items for the task
            
        Returns:
            Task name for updates
        """
        task_id = self.progress.add_task(f"  └─ {description}", total=total)
        self.sub_tasks[name] = task_id
        return name
        
    def update_subtask(self, name: str, **kwargs):
        """Update a subtask.
        
        Args:
            name: Task name
            **kwargs: Update arguments
        """
        if name in self.sub_tasks:
            # Route through throttler if enabled, otherwise update directly
            if self.throttler and self.throttler.running:
                self.throttler.update(name, **kwargs)
            else:
                self.progress.update(self.sub_tasks[name], **kwargs)
                
    def _direct_update_subtask(self, name: str, **kwargs):
        """Direct subtask update bypassing throttler (used by throttler itself)."""
        if name in self.sub_tasks:
            self.progress.update(self.sub_tasks[name], **kwargs)
            
    def update_stage(self, stage: str, description: str = ""):
        """Update the current stage of processing.
        
        Args:
            stage: Stage name
            description: Optional description
        """
        if description:
            self.update_main(description=f"[bold blue]{stage}[/bold blue]: {description}")
        else:
            self.update_main(description=f"[bold blue]{stage}[/bold blue]")
    
    def set_status(self, status: str):
        """Set a status message.
        
        Args:
            status: Status message to display
        """
        self.update_main(description=status)
    
    def update_metrics(self, metrics: dict):
        """Update metrics display.
        
        Args:
            metrics: Dictionary of metrics to display
        """
        # Create a summary description from metrics
        metric_parts = []
        if 'records_stored' in metrics:
            metric_parts.append(f"Stored: {metrics['records_stored']}")
        if 'records_quarantined' in metrics:
            metric_parts.append(f"Quarantined: {metrics['records_quarantined']}")
        if 'errors_encountered' in metrics:
            metric_parts.append(f"Errors: {metrics['errors_encountered']}")
        
        if metric_parts:
            summary = " | ".join(metric_parts)
            self.update_main(description=f"[green]{summary}[/green]")
    
    def log(self, message: str, style: str = "dim"):
        """Log a message within the progress context.
        
        Args:
            message: Message to log
            style: Rich style for the message
        """
        self.progress.console.print(f"[{style}]{message}[/{style}]")


class MetricsDisplay:
    """Live metrics display for operations with real-time system monitoring."""
    
    def __init__(self, title: str = "Operation Metrics", 
                 show_system_metrics: bool = True,
                 show_operation_metrics: bool = True):
        """Initialize metrics display.
        
        Args:
            title: Display title
            show_system_metrics: Whether to show CPU/memory/network metrics
            show_operation_metrics: Whether to show operation-specific metrics
        """
        self.title = title
        self.metrics = {}
        self.start_time = time.time()
        self.show_system_metrics = show_system_metrics
        self.show_operation_metrics = show_operation_metrics
        
        # System metrics tracking
        self.process = psutil.Process(os.getpid())
        self.last_net_io = psutil.net_io_counters()
        self.last_net_time = time.time()
        self.network_speeds = deque(maxlen=10)  # Track last 10 network speed measurements
        
        # Error tracking
        self.error_count = 0
        self.warning_count = 0
        self.last_error = None
        
        # Throughput tracking
        self.throughput_history = deque(maxlen=20)
        self.last_throughput_update = time.time()
        self.last_records_count = 0
        
    @contextmanager
    def live_display(self):
        """Context manager for live display."""
        with Live(self._generate_display(), console=console, refresh_per_second=2) as live:
            self.live = live
            yield self
            
    def update(self, **metrics):
        """Update metrics.
        
        Args:
            **metrics: Key-value pairs of metrics
        """
        # Update operation metrics
        self.metrics.update(metrics)
        
        # Track errors/warnings
        if 'errors' in metrics:
            self.error_count = metrics['errors']
        if 'warnings' in metrics:
            self.warning_count = metrics['warnings']
        if 'last_error' in metrics:
            self.last_error = metrics['last_error']
            
        # Calculate throughput if records_processed is provided
        if 'records_processed' in metrics:
            current_time = time.time()
            time_delta = current_time - self.last_throughput_update
            if time_delta > 0.5:  # Update throughput every 0.5 seconds
                records_delta = metrics['records_processed'] - self.last_records_count
                if records_delta > 0:
                    throughput = records_delta / time_delta
                    self.throughput_history.append(throughput)
                    self.last_records_count = metrics['records_processed']
                    self.last_throughput_update = current_time
        
        if hasattr(self, 'live'):
            self.live.update(self._generate_display())
            
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        metrics = {}
        
        try:
            # CPU usage (both process and system)
            metrics['cpu_percent'] = self.process.cpu_percent(interval=0.1)
            metrics['system_cpu_percent'] = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            process_memory = self.process.memory_info()
            system_memory = psutil.virtual_memory()
            metrics['process_memory_mb'] = process_memory.rss / 1024 / 1024
            metrics['system_memory_percent'] = system_memory.percent
            
            # Network I/O
            current_net_io = psutil.net_io_counters()
            current_time = time.time()
            time_delta = current_time - self.last_net_time
            
            if time_delta > 0:
                bytes_sent_delta = current_net_io.bytes_sent - self.last_net_io.bytes_sent
                bytes_recv_delta = current_net_io.bytes_recv - self.last_net_io.bytes_recv
                
                send_speed = bytes_sent_delta / time_delta
                recv_speed = bytes_recv_delta / time_delta
                
                self.network_speeds.append((send_speed, recv_speed))
                
                # Average of recent measurements for stability
                if self.network_speeds:
                    avg_send = sum(s[0] for s in self.network_speeds) / len(self.network_speeds)
                    avg_recv = sum(s[1] for s in self.network_speeds) / len(self.network_speeds)
                    metrics['network_send_mbps'] = avg_send / 1024 / 1024
                    metrics['network_recv_mbps'] = avg_recv / 1024 / 1024
                
                self.last_net_io = current_net_io
                self.last_net_time = current_time
                
        except Exception:
            # Don't fail if we can't get system metrics
            pass
            
        return metrics
            
    def _generate_display(self) -> Layout:
        """Generate the display layout with multiple panels."""
        layout = Layout()
        
        # Create sections based on what's enabled
        sections = []
        
        if self.show_operation_metrics:
            sections.append(self._generate_operation_panel())
            
        if self.show_system_metrics:
            sections.append(self._generate_system_panel())
            
        # Add error panel if there are errors
        if self.error_count > 0 or self.warning_count > 0:
            sections.append(self._generate_error_panel())
            
        # Use columns for side-by-side display
        if len(sections) > 1:
            return Panel(Columns(sections, equal=True), title=self.title, border_style="blue")
        elif sections:
            return sections[0]
        else:
            return Panel("No metrics to display", title=self.title, border_style="blue")
    
    def _generate_operation_panel(self) -> Panel:
        """Generate operation metrics panel."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Value", style="bold")
        
        # Add elapsed time
        elapsed = timedelta(seconds=int(time.time() - self.start_time))
        table.add_row("⏱️  Elapsed Time", str(elapsed))
        
        # Calculate average throughput
        if self.throughput_history:
            avg_throughput = sum(self.throughput_history) / len(self.throughput_history)
            table.add_row("📈 Avg Throughput", f"{avg_throughput:,.0f} rec/s")
        
        # Add all operation metrics
        for key, value in sorted(self.metrics.items()):
            if key not in ['errors', 'warnings', 'last_error', 'records_processed']:
                # Format the key
                formatted_key = key.replace('_', ' ').title()
                
                # Add emoji based on metric type
                if 'record' in key.lower():
                    formatted_key = f"📊 {formatted_key}"
                elif 'chunk' in key.lower():
                    formatted_key = f"📦 {formatted_key}"
                elif 'api' in key.lower():
                    formatted_key = f"🌐 {formatted_key}"
                
                # Format the value
                if isinstance(value, (int, float)):
                    if value > 1_000_000:
                        formatted_value = f"{value/1_000_000:.2f}M"
                    elif value > 1_000:
                        formatted_value = f"{value/1_000:.2f}K"
                    else:
                        formatted_value = f"{value:,.0f}"
                else:
                    formatted_value = str(value)
                    
                table.add_row(formatted_key, formatted_value)
                
        return Panel(table, title="📊 Operation Metrics", border_style="green")
    
    def _generate_system_panel(self) -> Panel:
        """Generate system metrics panel."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Value", style="bold")
        
        # Get current system metrics
        sys_metrics = self._get_system_metrics()
        
        # CPU
        if 'cpu_percent' in sys_metrics:
            cpu_style = "green" if sys_metrics['cpu_percent'] < 50 else "yellow" if sys_metrics['cpu_percent'] < 80 else "red"
            table.add_row("🖥️  Process CPU", f"[{cpu_style}]{sys_metrics['cpu_percent']:.1f}%[/{cpu_style}]")
            table.add_row("💻 System CPU", f"{sys_metrics['system_cpu_percent']:.1f}%")
            
        # Memory
        if 'process_memory_mb' in sys_metrics:
            mem_style = "green" if sys_metrics['process_memory_mb'] < 500 else "yellow" if sys_metrics['process_memory_mb'] < 1000 else "red"
            table.add_row("🧠 Process Memory", f"[{mem_style}]{sys_metrics['process_memory_mb']:.1f} MB[/{mem_style}]")
            table.add_row("💾 System Memory", f"{sys_metrics['system_memory_percent']:.1f}%")
            
        # Network
        if 'network_recv_mbps' in sys_metrics:
            table.add_row("⬇️  Download Speed", f"{sys_metrics['network_recv_mbps']:.2f} MB/s")
            table.add_row("⬆️  Upload Speed", f"{sys_metrics['network_send_mbps']:.2f} MB/s")
            
        return Panel(table, title="💻 System Metrics", border_style="blue")
    
    def _generate_error_panel(self) -> Panel:
        """Generate error/warning panel."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Type", style="cyan", width=20)
        table.add_column("Count", style="bold")
        
        if self.error_count > 0:
            table.add_row("❌ Errors", f"[red]{self.error_count}[/red]")
        if self.warning_count > 0:
            table.add_row("⚠️  Warnings", f"[yellow]{self.warning_count}[/yellow]")
            
        if self.last_error:
            table.add_row("", f"[dim]{self.last_error[:40]}...[/dim]")
            
        return Panel(table, title="⚠️  Issues", border_style="red" if self.error_count > 0 else "yellow")


class BatchProgressTracker:
    """Track progress for batch operations."""
    
    def __init__(self, total_batches: int, items_per_batch: Optional[int] = None):
        """Initialize batch progress tracker.
        
        Args:
            total_batches: Total number of batches
            items_per_batch: Items per batch (if known)
        """
        self.total_batches = total_batches
        self.items_per_batch = items_per_batch
        self.current_batch = 0
        self.total_items_processed = 0
        self.batch_times = []
        self.start_time = time.time()
        
    @contextmanager
    def track_batch(self, batch_num: int, batch_size: Optional[int] = None):
        """Track a single batch operation.
        
        Args:
            batch_num: Batch number (1-indexed)
            batch_size: Size of this batch
            
        Yields:
            Batch context
        """
        batch_start = time.time()
        self.current_batch = batch_num
        
        try:
            yield self
        finally:
            batch_time = time.time() - batch_start
            self.batch_times.append(batch_time)
            if batch_size:
                self.total_items_processed += batch_size
                
    def get_stats(self) -> Dict[str, Any]:
        """Get batch processing statistics.
        
        Returns:
            Dictionary of statistics
        """
        if not self.batch_times:
            return {}
            
        avg_batch_time = sum(self.batch_times) / len(self.batch_times)
        total_time = time.time() - self.start_time
        
        stats = {
            'batches_completed': len(self.batch_times),
            'total_batches': self.total_batches,
            'avg_batch_time': avg_batch_time,
            'total_time': total_time,
            'items_processed': self.total_items_processed,
        }
        
        # Calculate ETA
        if self.current_batch < self.total_batches:
            remaining_batches = self.total_batches - self.current_batch
            eta_seconds = remaining_batches * avg_batch_time
            stats['eta'] = timedelta(seconds=int(eta_seconds))
            
        # Calculate throughput
        if total_time > 0:
            stats['batches_per_second'] = len(self.batch_times) / total_time
            if self.total_items_processed > 0:
                stats['items_per_second'] = self.total_items_processed / total_time
                
        return stats


def create_progress_bar(description: str, total: Optional[int] = None,
                       **kwargs) -> EnhancedProgress:
    """Create an enhanced progress bar with configuration defaults.
    
    Args:
        description: Progress bar description
        total: Total items (if known)
        **kwargs: Additional options (override configuration)
        
    Returns:
        EnhancedProgress instance
    """
    # Configuration is automatically applied in EnhancedProgress.__init__
    progress = EnhancedProgress(description, **kwargs)
    return progress


def create_configured_progress(description: str, progress_style: str = None) -> EnhancedProgress:
    """Create a progress bar optimized for the current environment and configuration.
    
    Args:
        description: Progress bar description
        progress_style: Override progress style (simple, advanced, compact, minimal)
        
    Returns:
        EnhancedProgress instance configured for optimal performance
    """
    # Get configuration or detect environment
    if progress_style is None:
        progress_style = _get_config_setting('progress.style', 'advanced')
    
    # Configure based on style
    if progress_style == 'simple':
        return EnhancedProgress(
            description,
            show_speed=False,
            show_eta=True,
            show_records=False,
            use_adaptive_eta=False,
            use_throttling=False
        )
    elif progress_style == 'minimal':
        return EnhancedProgress(
            description,
            show_speed=False,
            show_eta=False,
            show_records=False,
            use_adaptive_eta=False,
            use_throttling=False
        )
    elif progress_style == 'compact':
        return EnhancedProgress(
            description,
            show_speed=True,
            show_eta=True,
            show_records=False,
            use_adaptive_eta=True,
            use_throttling=True
        )
    else:  # advanced (default)
        return EnhancedProgress(
            description,
            show_speed=True,
            show_eta=True,
            show_records=True,
            use_adaptive_eta=True,
            use_throttling=True
        )


def format_bytes(bytes_value: int) -> str:
    """Format bytes into human-readable string.
    
    Args:
        bytes_value: Number of bytes
        
    Returns:
        Formatted string
    """
    if bytes_value > 1_000_000_000:
        return f"{bytes_value/1_000_000_000:.2f} GB"
    elif bytes_value > 1_000_000:
        return f"{bytes_value/1_000_000:.2f} MB"
    elif bytes_value > 1_000:
        return f"{bytes_value/1_000:.2f} KB"
    else:
        return f"{bytes_value} B"


def format_duration(seconds: float) -> str:
    """Format duration into human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"


class ProgressWithMetrics:
    """Combined progress bar and metrics display for comprehensive monitoring."""
    
    def __init__(self, description: str = "", 
                 show_metrics: bool = True,
                 metrics_position: str = "above",
                 use_throttling: bool = False,
                 throttle_min_interval: float = 0.1):
        """Initialize combined progress and metrics display.
        
        Args:
            description: Progress bar description
            show_metrics: Whether to show metrics panel
            metrics_position: Position of metrics ("above", "below", "side")
            use_throttling: Whether to throttle high-frequency updates
            throttle_min_interval: Minimum throttling interval (seconds)
        """
        self.description = description
        self.show_metrics = show_metrics
        self.metrics_position = metrics_position
        
        # Initialize components
        self.progress = EnhancedProgress(
            description,
            show_speed=True,
            show_eta=True,
            show_records=True,
            use_adaptive_eta=True,
            use_throttling=use_throttling,
            throttle_min_interval=throttle_min_interval
        )
        
        if show_metrics:
            self.metrics_display = MetricsDisplay(
                title="Pipeline Metrics",
                show_system_metrics=True,
                show_operation_metrics=True
            )
        else:
            self.metrics_display = None
            
        self.layout = None
        self.live = None
        
    def __enter__(self):
        """Enter context manager."""
        if self.show_metrics and self.metrics_position in ["above", "side"]:
            # Create layout for combined display
            self.layout = Layout()
            
            if self.metrics_position == "above":
                self.layout.split_column(
                    Layout(name="metrics", size=10),
                    Layout(name="progress", size=3)
                )
            else:  # side
                self.layout.split_row(
                    Layout(name="progress", ratio=2),
                    Layout(name="metrics", ratio=1)
                )
                
            # Start live display
            self.live = Live(self.layout, console=console, refresh_per_second=2)
            self.live.__enter__()
            
            # Start progress within the layout
            self.progress.__enter__()
            
            # Update layout with initial content
            self._update_layout()
        else:
            # Just use regular progress bar
            self.progress.__enter__()
            
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self.live:
            self.live.__exit__(exc_type, exc_val, exc_tb)
        else:
            self.progress.__exit__(exc_type, exc_val, exc_tb)
            
    def update_progress(self, **kwargs):
        """Update progress bar.
        
        Args:
            **kwargs: Arguments for EnhancedProgress.update_main
        """
        self.progress.update_main(**kwargs)
        self._update_layout()
        
    def update_metrics(self, **metrics):
        """Update metrics display.
        
        Args:
            **metrics: Metrics to update
        """
        if self.metrics_display:
            self.metrics_display.update(**metrics)
            self._update_layout()
            
    def log(self, message: str, style: str = "dim"):
        """Log a message.
        
        Args:
            message: Message to log
            style: Rich style
        """
        if self.live:
            # Temporarily pause live display
            self.live.stop()
            console.print(f"[{style}]{message}[/{style}]")
            self.live.start()
        else:
            self.progress.log(message, style)
            
    def _update_layout(self):
        """Update the layout with current content."""
        if self.layout and self.metrics_display:
            # Get progress display
            progress_display = Panel(
                self.progress.progress,
                border_style="green"
            )
            
            # Get metrics display
            metrics_display = self.metrics_display._generate_display()
            
            # Update layout
            if self.metrics_position == "above":
                self.layout["metrics"].update(metrics_display)
                self.layout["progress"].update(progress_display)
            else:  # side
                self.layout["progress"].update(progress_display)
                self.layout["metrics"].update(metrics_display)


class ThrottledProgressUpdater:
    """Throttle progress updates for better performance and smoother UI.
    
    This class prevents UI freezing with high-frequency updates by batching
    updates and using adaptive frequency based on operation speed.
    """
    
    def __init__(self, min_interval: float = 0.1, max_interval: float = 1.0,
                 adaptive: bool = True, max_queue_size: int = 1000):
        """Initialize throttled progress updater.
        
        Args:
            min_interval: Minimum time between updates (seconds)
            max_interval: Maximum time between updates (seconds)
            adaptive: Whether to use adaptive interval calculation
            max_queue_size: Maximum number of pending updates to queue
        """
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.adaptive = adaptive
        self.max_queue_size = max_queue_size
        
        # Update tracking
        self.last_update_time = 0
        self.pending_updates: Dict[str, Dict[str, Any]] = {}
        self.update_queue = queue.Queue(maxsize=max_queue_size)
        self.running = False
        self.update_thread = None
        
        # Performance tracking for adaptive intervals
        self.update_frequency_history = deque(maxlen=50)
        self.load_history = deque(maxlen=20)
        
        # Target progress instance
        self.progress_instance = None
        self.update_method = "update_main"
        
    def set_target(self, progress_instance: Any, update_method: str = "update_main"):
        """Set the target progress instance to update.
        
        Args:
            progress_instance: Progress instance (EnhancedProgress, ProgressWithMetrics, etc.)
            update_method: Method name to call for updates
        """
        self.progress_instance = progress_instance
        self.update_method = update_method
        
    def start(self):
        """Start the throttled updater thread."""
        if self.running:
            return
            
        self.running = True
        self.update_thread = threading.Thread(target=self._update_worker, daemon=True)
        self.update_thread.start()
        
    def stop(self):
        """Stop the throttled updater and flush remaining updates."""
        if not self.running:
            return
            
        self.running = False
        
        # Signal the worker to stop
        try:
            self.update_queue.put(None, timeout=0.1)
        except queue.Full:
            pass
            
        # Wait for worker thread to finish
        if self.update_thread:
            self.update_thread.join(timeout=1.0)
            
        # Flush any remaining updates
        self._flush_updates()
        
    def update(self, task_id: str = "main", **kwargs):
        """Queue an update for throttled delivery.
        
        Args:
            task_id: Identifier for the task being updated
            **kwargs: Update parameters
        """
        current_time = time.time()
        
        # Store pending update (overwrites previous for same task)
        if task_id not in self.pending_updates:
            self.pending_updates[task_id] = {}
        self.pending_updates[task_id].update(kwargs)
        self.pending_updates[task_id]['_timestamp'] = current_time
        
        # Track update frequency for adaptive behavior
        if self.update_frequency_history:
            time_since_last = current_time - self.update_frequency_history[-1]
            self.update_frequency_history.append(current_time)
        else:
            self.update_frequency_history.append(current_time)
        
        # Calculate appropriate interval
        update_interval = self._calculate_update_interval()
        time_since_last_update = current_time - self.last_update_time
        
        # Check if we should flush updates
        should_flush = (
            time_since_last_update >= update_interval or
            len(self.pending_updates) >= 10 or  # Batch size limit
            not self.running  # Not throttling
        )
        
        if should_flush:
            try:
                # Put update signal in queue (non-blocking)
                self.update_queue.put("flush", block=False)
            except queue.Full:
                # Queue is full, force immediate flush
                self._flush_updates()
                
    def _calculate_update_interval(self) -> float:
        """Calculate the appropriate update interval based on current conditions."""
        if not self.adaptive:
            return self.min_interval
            
        # Calculate update frequency (updates per second)
        if len(self.update_frequency_history) < 2:
            return self.min_interval
            
        # Get recent update frequency
        recent_updates = list(self.update_frequency_history)[-10:]
        if len(recent_updates) < 2:
            return self.min_interval
            
        time_span = recent_updates[-1] - recent_updates[0]
        update_rate = len(recent_updates) / max(time_span, 0.1)
        
        # Track system load (simplified using CPU usage)
        try:
            cpu_percent = psutil.cpu_percent(interval=0)
            self.load_history.append(cpu_percent)
            avg_load = sum(self.load_history) / len(self.load_history)
        except:
            avg_load = 0
            
        # Adaptive interval calculation
        base_interval = self.min_interval
        
        # Increase interval if high update rate
        if update_rate > 20:  # More than 20 updates/second
            base_interval *= min(2.0, update_rate / 20)
            
        # Increase interval if high system load
        if avg_load > 70:
            base_interval *= 1.5
        elif avg_load > 90:
            base_interval *= 2.0
            
        # Clamp to min/max bounds
        return max(self.min_interval, min(self.max_interval, base_interval))
        
    def _update_worker(self):
        """Worker thread that processes batched updates."""
        while self.running:
            try:
                # Wait for flush signal or timeout
                signal = self.update_queue.get(timeout=self.max_interval)
                
                if signal is None:  # Stop signal
                    break
                    
                if signal == "flush":
                    self._flush_updates()
                    
            except queue.Empty:
                # Timeout - flush any pending updates
                if self.pending_updates:
                    self._flush_updates()
                    
    def _flush_updates(self):
        """Flush all pending updates."""
        if not self.pending_updates:
            return
            
        if not self.progress_instance:
            # Clear pending updates even if there's no target
            self.pending_updates.clear()
            self.last_update_time = time.time()
            return
            
        current_time = time.time()
        
        # Apply all pending updates
        for task_id, update_data in self.pending_updates.items():
            if not update_data:
                continue
                
            # Remove internal timestamp
            update_kwargs = {k: v for k, v in update_data.items() if not k.startswith('_')}
            
            try:
                if hasattr(self.progress_instance, self.update_method):
                    update_func = getattr(self.progress_instance, self.update_method)
                    
                    # Handle different update signatures
                    if task_id == "main":
                        # Use direct update method if available to avoid throttling recursion
                        if hasattr(self.progress_instance, '_direct_update_main'):
                            self.progress_instance._direct_update_main(**update_kwargs)
                        else:
                            update_func(**update_kwargs)
                    else:
                        # For subtask updates, use direct method if available
                        if hasattr(self.progress_instance, '_direct_update_subtask'):
                            self.progress_instance._direct_update_subtask(task_id, **update_kwargs)
                        elif hasattr(self.progress_instance, 'update_subtask'):
                            self.progress_instance.update_subtask(task_id, **update_kwargs)
                        elif hasattr(self.progress_instance, 'update_progress'):
                            self.progress_instance.update_progress(**update_kwargs)
                        else:
                            update_func(**update_kwargs)
                            
            except Exception:
                # Don't let update failures break the throttler
                pass
                
        # Clear pending updates and track flush time
        self.pending_updates.clear()
        self.last_update_time = current_time
        
    def get_stats(self) -> Dict[str, Any]:
        """Get throttling statistics.
        
        Returns:
            Dictionary with throttling performance stats
        """
        stats = {
            'running': self.running,
            'pending_updates': len(self.pending_updates),
            'queue_size': self.update_queue.qsize() if hasattr(self.update_queue, 'qsize') else 0,
            'min_interval': self.min_interval,
            'max_interval': self.max_interval,
            'adaptive': self.adaptive,
        }
        
        if self.update_frequency_history:
            recent_updates = list(self.update_frequency_history)[-10:]
            if len(recent_updates) >= 2:
                time_span = recent_updates[-1] - recent_updates[0]
                update_rate = len(recent_updates) / max(time_span, 0.1)
                stats['update_rate'] = update_rate
                
        if self.load_history:
            stats['avg_system_load'] = sum(self.load_history) / len(self.load_history)
            
        current_interval = self._calculate_update_interval()
        stats['current_interval'] = current_interval
        
        return stats
        
    def __enter__(self):
        """Enter context manager - start throttling."""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager - stop throttling and flush."""
        self.stop()


class StreamingProgressTracker:
    """Memory-efficient progress tracking for large operations.
    
    Uses streaming techniques and circular buffers to handle massive
    datasets without consuming excessive memory.
    """
    
    def __init__(self, max_history: int = 1000, checkpoint_interval: int = 100):
        """Initialize streaming progress tracker.
        
        Args:
            max_history: Maximum number of metrics to keep in memory
            checkpoint_interval: How often to create progress checkpoints
        """
        self.max_history = max_history
        self.checkpoint_interval = checkpoint_interval
        
        # Circular buffers for efficient memory usage
        self.metrics_buffer = deque(maxlen=max_history)
        self.throughput_buffer = deque(maxlen=100)
        self.error_buffer = deque(maxlen=50)
        
        # Checkpoints for recovery and analysis
        self.checkpoints: Dict[str, Dict[str, Any]] = {}
        self.checkpoint_counter = 0
        
        # Stream processing state
        self.start_time = time.time()
        self.total_processed = 0
        self.last_checkpoint_time = self.start_time
        self.last_metric_time = self.start_time
        
        # Compression for efficient storage
        self.compression_enabled = True
        
    def record_metric(self, metric_type: str, value: float, 
                     timestamp: Optional[float] = None, metadata: Optional[Dict] = None):
        """Record a metric efficiently using streaming approach.
        
        Args:
            metric_type: Type of metric (e.g., 'throughput', 'error_rate')
            value: Metric value
            timestamp: Optional timestamp (uses current time if None)
            metadata: Optional metadata for the metric
        """
        timestamp = timestamp or time.time()
        
        # Compress metric data for memory efficiency
        if self.compression_enabled:
            metric_data = {
                't': int((timestamp - self.start_time) * 1000),  # ms since start
                'v': round(value, 3),  # Limit precision to save space
                'm': metric_type[:8]  # Truncate long type names
            }
            if metadata:
                # Store only essential metadata
                metric_data['meta'] = {k: v for k, v in metadata.items() 
                                     if k in ['symbol', 'schema', 'chunk_id']}
        else:
            metric_data = {
                'timestamp': timestamp,
                'value': value,
                'type': metric_type,
                'metadata': metadata
            }
        
        # Add to circular buffer (automatically removes old entries)
        self.metrics_buffer.append(metric_data)
        
        # Track throughput specifically
        if metric_type == 'throughput':
            self.throughput_buffer.append((timestamp, value))
            
        # Track errors separately
        if 'error' in metric_type.lower():
            self.error_buffer.append({'time': timestamp, 'value': value, 'type': metric_type})
            
        # Create checkpoint if needed
        self.checkpoint_counter += 1
        if self.checkpoint_counter % self.checkpoint_interval == 0:
            self.create_checkpoint(f"auto_{self.checkpoint_counter // self.checkpoint_interval}")
            
        self.last_metric_time = timestamp
        
    def create_checkpoint(self, name: str, custom_data: Optional[Dict] = None):
        """Create a progress checkpoint for recovery and analysis.
        
        Args:
            name: Checkpoint name
            custom_data: Optional custom data to include
        """
        current_time = time.time()
        
        checkpoint = {
            'timestamp': current_time,
            'total_processed': self.total_processed,
            'metrics_count': len(self.metrics_buffer),
            'elapsed_time': current_time - self.start_time,
            'current_metrics': self.get_current_metrics(),
        }
        
        if custom_data:
            checkpoint['custom'] = custom_data
            
        self.checkpoints[name] = checkpoint
        
        # Keep only recent checkpoints to limit memory usage
        if len(self.checkpoints) > 20:
            oldest_checkpoint = min(self.checkpoints.keys(), 
                                  key=lambda k: self.checkpoints[k]['timestamp'])
            del self.checkpoints[oldest_checkpoint]
            
        self.last_checkpoint_time = current_time
        
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current aggregated metrics.
        
        Returns:
            Dictionary of current performance metrics
        """
        current_time = time.time()
        
        # Calculate throughput from recent data
        recent_throughput = 0
        if self.throughput_buffer:
            recent_values = [v for t, v in self.throughput_buffer if current_time - t < 60]
            if recent_values:
                recent_throughput = sum(recent_values) / len(recent_values)
                
        # Calculate error rate
        error_rate = 0
        if self.error_buffer:
            recent_errors = [e for e in self.error_buffer if current_time - e['time'] < 300]
            error_rate = len(recent_errors) / min(300, current_time - self.start_time)
            
        # Overall stats
        total_elapsed = current_time - self.start_time
        
        return {
            'elapsed_time': total_elapsed,
            'total_processed': self.total_processed,
            'metrics_recorded': len(self.metrics_buffer),
            'avg_throughput': self.total_processed / total_elapsed if total_elapsed > 0 else 0,
            'recent_throughput': recent_throughput,
            'error_rate': error_rate,
            'memory_usage_mb': self._estimate_memory_usage(),
            'checkpoints_created': len(self.checkpoints),
        }
        
    def get_streaming_stats(self, window_seconds: int = 60) -> Dict[str, Any]:
        """Get streaming statistics for a time window.
        
        Args:
            window_seconds: Time window to analyze (seconds)
            
        Returns:
            Statistics for the specified time window
        """
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # Filter metrics to window
        window_metrics = []
        for metric in self.metrics_buffer:
            if self.compression_enabled:
                metric_time = self.start_time + (metric['t'] / 1000)
            else:
                metric_time = metric['timestamp']
                
            if metric_time >= window_start:
                window_metrics.append(metric)
                
        if not window_metrics:
            return {'window_seconds': window_seconds, 'metrics_count': 0}
            
        # Analyze window metrics
        metric_types = {}
        for metric in window_metrics:
            if self.compression_enabled:
                metric_type = metric['m']
                value = metric['v']
            else:
                metric_type = metric['type']
                value = metric['value']
                
            if metric_type not in metric_types:
                metric_types[metric_type] = []
            metric_types[metric_type].append(value)
            
        # Calculate statistics
        stats = {
            'window_seconds': window_seconds,
            'metrics_count': len(window_metrics),
            'metric_types': list(metric_types.keys()),
        }
        
        for metric_type, values in metric_types.items():
            stats[f'{metric_type}_count'] = len(values)
            stats[f'{metric_type}_avg'] = sum(values) / len(values)
            stats[f'{metric_type}_min'] = min(values)
            stats[f'{metric_type}_max'] = max(values)
            
        return stats
        
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB.
        
        Returns:
            Estimated memory usage in megabytes
        """
        # Rough estimation based on buffer sizes and data structures
        metrics_size = len(self.metrics_buffer) * 100  # ~100 bytes per metric
        throughput_size = len(self.throughput_buffer) * 24  # ~24 bytes per entry
        error_size = len(self.error_buffer) * 50  # ~50 bytes per error
        checkpoint_size = len(self.checkpoints) * 500  # ~500 bytes per checkpoint
        
        total_bytes = metrics_size + throughput_size + error_size + checkpoint_size
        return total_bytes / (1024 * 1024)
        
    def export_metrics(self, file_path: Path, format: str = "json", 
                      include_checkpoints: bool = True):
        """Export metrics to file for analysis.
        
        Args:
            file_path: Path to export file
            format: Export format ("json", "csv")
            include_checkpoints: Whether to include checkpoint data
        """
        try:
            if format.lower() == "json":
                export_data = {
                    'metadata': {
                        'start_time': self.start_time,
                        'export_time': time.time(),
                        'total_processed': self.total_processed,
                        'compression_enabled': self.compression_enabled,
                    },
                    'metrics': list(self.metrics_buffer),
                    'current_stats': self.get_current_metrics(),
                }
                
                if include_checkpoints:
                    export_data['checkpoints'] = self.checkpoints
                    
                with open(file_path, 'w') as f:
                    json.dump(export_data, f, indent=2)
                    
            elif format.lower() == "csv":
                import csv
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    
                    # Write header
                    if self.compression_enabled:
                        writer.writerow(['timestamp_ms', 'value', 'type'])
                        for metric in self.metrics_buffer:
                            writer.writerow([metric['t'], metric['v'], metric['m']])
                    else:
                        writer.writerow(['timestamp', 'value', 'type'])
                        for metric in self.metrics_buffer:
                            writer.writerow([metric['timestamp'], metric['value'], metric['type']])
                            
        except Exception:
            # Don't fail the main operation if export fails
            pass
            
    def clear_history(self, keep_recent_seconds: int = 300):
        """Clear old metrics to free memory.
        
        Args:
            keep_recent_seconds: How many seconds of recent data to keep
        """
        if not self.metrics_buffer:
            return
            
        current_time = time.time()
        cutoff_time = current_time - keep_recent_seconds
        
        # Filter metrics to keep only recent ones
        recent_metrics = []
        for metric in self.metrics_buffer:
            if self.compression_enabled:
                metric_time = self.start_time + (metric['t'] / 1000)
            else:
                metric_time = metric['timestamp']
                
            if metric_time >= cutoff_time:
                recent_metrics.append(metric)
                
        # Replace buffer with recent metrics
        self.metrics_buffer.clear()
        self.metrics_buffer.extend(recent_metrics)
        
        # Clean up other buffers
        self.throughput_buffer = deque(
            [(t, v) for t, v in self.throughput_buffer if t >= cutoff_time],
            maxlen=self.throughput_buffer.maxlen
        )
        
        self.error_buffer = deque(
            [e for e in self.error_buffer if e['time'] >= cutoff_time],
            maxlen=self.error_buffer.maxlen
        )


class OperationMonitor:
    """Monitor and track background operations across CLI sessions.
    
    This class provides persistent tracking of operations, allowing users
    to monitor long-running tasks even across CLI restarts.
    """
    
    def __init__(self, state_dir: Optional[Path] = None):
        """Initialize operation monitor.
        
        Args:
            state_dir: Directory for persistent state storage
        """
        self.state_dir = state_dir or Path.home() / ".hdi_state"
        self.state_dir.mkdir(exist_ok=True)
        
        # In-memory operation tracking
        self.operations: Dict[str, Dict[str, Any]] = {}
        self.load_operations()
        
    def register_operation(self, operation_id: str, config: Dict[str, Any]) -> str:
        """Register a new operation for monitoring.
        
        Args:
            operation_id: Unique identifier for the operation
            config: Operation configuration
            
        Returns:
            Operation ID for tracking
        """
        operation = {
            'id': operation_id,
            'config': config,
            'status': 'starting',
            'start_time': datetime.now().isoformat(),
            'pid': os.getpid(),
            'progress': 0,
            'total': config.get('total_items', 0),
            'metrics': {},
            'errors': [],
            'last_update': datetime.now().isoformat(),
        }
        
        # Store in memory and persist to disk
        self.operations[operation_id] = operation
        self._persist_operation(operation_id, operation)
        
        return operation_id
        
    def update_operation(self, operation_id: str, **updates):
        """Update an operation's status and metrics.
        
        Args:
            operation_id: Operation identifier
            **updates: Fields to update
        """
        if operation_id not in self.operations:
            return
            
        operation = self.operations[operation_id]
        
        # Update fields
        for key, value in updates.items():
            if key == 'metrics':
                operation['metrics'].update(value)
            elif key == 'errors':
                if isinstance(value, list):
                    operation['errors'].extend(value)
                else:
                    operation['errors'].append(value)
            else:
                operation[key] = value
                
        operation['last_update'] = datetime.now().isoformat()
        
        # Persist changes
        self._persist_operation(operation_id, operation)
        
    def complete_operation(self, operation_id: str, status: str = 'completed', 
                          final_metrics: Optional[Dict] = None):
        """Mark an operation as completed.
        
        Args:
            operation_id: Operation identifier
            status: Final status ('completed', 'failed', 'cancelled')
            final_metrics: Final metrics summary
        """
        if operation_id not in self.operations:
            return
            
        operation = self.operations[operation_id]
        operation['status'] = status
        operation['end_time'] = datetime.now().isoformat()
        operation['progress'] = operation.get('total', 100)
        
        if final_metrics:
            operation['metrics'].update(final_metrics)
            
        # Calculate duration
        start_time = datetime.fromisoformat(operation['start_time'])
        end_time = datetime.fromisoformat(operation['end_time'])
        operation['duration_seconds'] = (end_time - start_time).total_seconds()
        
        self._persist_operation(operation_id, operation)
        
    def get_active_operations(self) -> List[Dict[str, Any]]:
        """Get all currently active operations.
        
        Returns:
            List of active operation dictionaries
        """
        active = []
        
        for operation in self.operations.values():
            # Check if process is still running for active operations
            if operation['status'] in ['starting', 'running', 'in_progress']:
                if self._is_process_running(operation['pid']):
                    active.append(operation.copy())
                else:
                    # Process died, mark as failed
                    operation['status'] = 'failed'
                    operation['end_time'] = datetime.now().isoformat()
                    operation['errors'].append("Process terminated unexpectedly")
                    self._persist_operation(operation['id'], operation)
                    
        return active
        
    def get_operation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent operation history.
        
        Args:
            limit: Maximum number of operations to return
            
        Returns:
            List of recent operations, most recent first
        """
        all_ops = list(self.operations.values())
        
        # Sort by start time, most recent first
        sorted_ops = sorted(all_ops, 
                          key=lambda op: op['start_time'], 
                          reverse=True)
        
        return sorted_ops[:limit]
        
    def cleanup_old_operations(self, days_old: int = 7):
        """Clean up old completed operations.
        
        Args:
            days_old: Remove operations older than this many days
        """
        cutoff_time = datetime.now() - timedelta(days=days_old)
        
        to_remove = []
        for op_id, operation in self.operations.items():
            if operation['status'] in ['completed', 'failed', 'cancelled']:
                end_time_str = operation.get('end_time')
                if end_time_str:
                    try:
                        end_time = datetime.fromisoformat(end_time_str)
                        if end_time < cutoff_time:
                            to_remove.append(op_id)
                    except:
                        pass
                        
        # Remove old operations
        for op_id in to_remove:
            del self.operations[op_id]
            operation_file = self.state_dir / f"{op_id}.json"
            if operation_file.exists():
                operation_file.unlink()
                
    def load_operations(self):
        """Load operations from persistent storage."""
        self.operations.clear()
        
        for op_file in self.state_dir.glob("*.json"):
            try:
                with open(op_file) as f:
                    operation = json.load(f)
                    self.operations[operation['id']] = operation
            except Exception:
                # Skip corrupted files
                continue
                
    def _persist_operation(self, operation_id: str, operation: Dict[str, Any]):
        """Persist operation to disk.
        
        Args:
            operation_id: Operation identifier
            operation: Operation data
        """
        try:
            operation_file = self.state_dir / f"{operation_id}.json"
            with open(operation_file, 'w') as f:
                json.dump(operation, f, indent=2)
        except Exception:
            # Don't fail if we can't persist
            pass
            
    def _is_process_running(self, pid: int) -> bool:
        """Check if a process is still running.
        
        Args:
            pid: Process ID
            
        Returns:
            True if process is running
        """
        try:
            import psutil
            return psutil.pid_exists(pid)
        except ImportError:
            # Fall back to basic check
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False


class LiveStatusDashboard:
    """Live dashboard for monitoring ongoing operations with multi-panel layout.
    
    Provides real-time status updates, system monitoring, and operation
    queue management in a professional dashboard layout.
    """
    
    def __init__(self, title: str = "📊 Historical Data Ingestor", 
                 show_system_metrics: bool = True,
                 show_operation_queue: bool = True,
                 refresh_rate: float = 2.0):
        """Initialize live status dashboard.
        
        Args:
            title: Dashboard title
            show_system_metrics: Whether to show system resource metrics
            show_operation_queue: Whether to show operation queue
            refresh_rate: Refresh rate in Hz
        """
        self.title = title
        self.show_system_metrics = show_system_metrics
        self.show_operation_queue = show_operation_queue
        self.refresh_rate = refresh_rate
        
        # Dashboard state
        self.current_status = "Ready"
        self.current_status_style = "cyan"
        self.operation_monitor = OperationMonitor()
        
        # Initialize layout
        self.layout = self._create_layout()
        
        # Metrics tracking
        self.system_metrics = {}
        self.last_system_update = 0
        self.process = psutil.Process(os.getpid())
        
        # Operation tracking
        self.current_operations = []
        self.operation_history = []
        
    def _create_layout(self) -> Layout:
        """Create the dashboard layout structure.
        
        Returns:
            Rich Layout object
        """
        layout = Layout()
        
        # Main structure: header, body, footer
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=4 if self.show_system_metrics else 2)
        )
        
        # Split body into main content and sidebar
        if self.show_operation_queue:
            layout["body"].split_row(
                Layout(name="main", ratio=2),
                Layout(name="sidebar", ratio=1)
            )
        else:
            layout["body"].update(Layout(name="main"))
            
        return layout
        
    @contextmanager
    def live_display(self):
        """Context manager for live dashboard display.
        
        Yields:
            Dashboard instance for updates
        """
        with Live(self.layout, console=console, refresh_per_second=self.refresh_rate) as live:
            self.live = live
            self._update_all_panels()
            yield self
            
    def update_status(self, status: str, style: str = "cyan"):
        """Update the current status message.
        
        Args:
            status: Status message
            style: Rich style for the message
        """
        self.current_status = status
        self.current_status_style = style
        self._update_header()
        
    def update_operation_progress(self, operation_id: str, **progress_data):
        """Update progress for a specific operation.
        
        Args:
            operation_id: Operation identifier
            **progress_data: Progress update data
        """
        # Update operation monitor
        self.operation_monitor.update_operation(operation_id, **progress_data)
        
        # Refresh active operations
        self._refresh_operations()
        self._update_main_panel()
        
    def add_operation(self, operation_id: str, config: Dict[str, Any]) -> str:
        """Add a new operation to track.
        
        Args:
            operation_id: Operation identifier
            config: Operation configuration
            
        Returns:
            Operation ID
        """
        op_id = self.operation_monitor.register_operation(operation_id, config)
        self._refresh_operations()
        self._update_all_panels()
        return op_id
        
    def complete_operation(self, operation_id: str, status: str = "completed", 
                          final_metrics: Optional[Dict] = None):
        """Mark an operation as completed.
        
        Args:
            operation_id: Operation identifier
            status: Final status
            final_metrics: Final metrics
        """
        self.operation_monitor.complete_operation(operation_id, status, final_metrics)
        self._refresh_operations()
        self._update_all_panels()
        
    def _refresh_operations(self):
        """Refresh operation lists from monitor."""
        self.current_operations = self.operation_monitor.get_active_operations()
        self.operation_history = self.operation_monitor.get_operation_history(limit=5)
        
    def _update_all_panels(self):
        """Update all dashboard panels."""
        self._update_header()
        self._update_main_panel()
        if self.show_operation_queue:
            self._update_sidebar()
        if self.show_system_metrics:
            self._update_footer()
            
        if hasattr(self, 'live'):
            self.live.update(self.layout)
            
    def _update_header(self):
        """Update header panel with status."""
        status_text = f"[{self.current_status_style}]Status: {self.current_status}[/{self.current_status_style}]"
        
        # Add operation summary
        active_count = len(self.current_operations)
        if active_count > 0:
            status_text += f" | [yellow]{active_count} active operation(s)[/yellow]"
            
        header_panel = Panel(
            status_text,
            title=self.title,
            border_style="blue",
            padding=(0, 1)
        )
        
        self.layout["header"].update(header_panel)
        
    def _update_main_panel(self):
        """Update main content panel."""
        if not self.current_operations:
            # No active operations
            content = Panel(
                "[dim]No active operations[/dim]\n\n"
                "[cyan]Use CLI commands to start data ingestion or queries[/cyan]",
                title="Current Operations",
                border_style="green",
                padding=(1, 2)
            )
        else:
            # Show active operations with progress
            content = self._create_operations_panel()
            
        if self.show_operation_queue:
            self.layout["main"].update(content)
        else:
            self.layout["body"].update(content)
            
    def _create_operations_panel(self) -> Panel:
        """Create panel showing current operations.
        
        Returns:
            Panel with operation details
        """
        table = Table(show_header=True, header_style="bold cyan", box=None)
        table.add_column("Operation", style="yellow", width=30)
        table.add_column("Progress", width=20)
        table.add_column("Status", width=15)
        table.add_column("ETA", width=10)
        table.add_column("Metrics", style="dim")
        
        for operation in self.current_operations:
            # Extract operation info
            op_name = operation['config'].get('description', operation['id'][:20])
            progress = operation.get('progress', 0)
            total = operation.get('total', 100)
            status = operation.get('status', 'unknown')
            
            # Format progress bar
            if total > 0:
                progress_pct = min(100, (progress / total) * 100)
                progress_bar = f"[green]{'█' * int(progress_pct // 5)}[/green]" + \
                              f"[dim]{'░' * (20 - int(progress_pct // 5))}[/dim]"
                progress_text = f"{progress_bar} {progress_pct:.1f}%"
            else:
                progress_text = "[dim]N/A[/dim]"
                
            # Format status with color
            status_color = {
                'running': 'green',
                'starting': 'yellow', 
                'in_progress': 'cyan',
                'failed': 'red',
                'completed': 'green'
            }.get(status, 'white')
            status_text = f"[{status_color}]{status}[/{status_color}]"
            
            # Calculate ETA
            eta_text = "[dim]--:--[/dim]"
            if status in ['running', 'in_progress'] and total > 0 and progress > 0:
                start_time = datetime.fromisoformat(operation['start_time'])
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > 0:
                    rate = progress / elapsed
                    if rate > 0:
                        remaining_time = (total - progress) / rate
                        eta_text = format_duration(remaining_time)
                        
            # Format metrics
            metrics = operation.get('metrics', {})
            key_metrics = []
            if 'records_processed' in metrics:
                key_metrics.append(f"Records: {metrics['records_processed']:,}")
            if 'throughput' in metrics:
                key_metrics.append(f"Rate: {metrics['throughput']:.0f}/s")
            if 'errors' in metrics:
                key_metrics.append(f"Errors: {metrics['errors']}")
                
            metrics_text = " | ".join(key_metrics) if key_metrics else "[dim]None[/dim]"
            
            table.add_row(op_name, progress_text, status_text, eta_text, metrics_text)
            
        return Panel(table, title="🔄 Active Operations", border_style="green")
        
    def _update_sidebar(self):
        """Update sidebar with operation queue and history."""
        try:
            # Check if sidebar exists in layout
            self.layout["sidebar"]
        except (KeyError, AttributeError):
            return
            
        # Create queue section
        queue_table = Table(show_header=False, box=None, padding=(0, 1))
        queue_table.add_column("Item", style="cyan")
        
        # Show next operations (placeholder for now)
        queue_table.add_row("📅 Daily update scheduled for tomorrow")
        queue_table.add_row("📊 Weekly report generation")
        queue_table.add_row("🧹 Cleanup old temp files")
        
        queue_panel = Panel(queue_table, title="📋 Queue", border_style="yellow")
        
        # Create history section
        history_table = Table(show_header=False, box=None, padding=(0, 1))
        history_table.add_column("Operation", style="dim", width=25)
        history_table.add_column("Status", width=8)
        
        for operation in self.operation_history:
            op_name = operation['config'].get('description', operation['id'][:20])
            status = operation.get('status', 'unknown')
            
            # Truncate name and add status icon
            short_name = op_name[:22] + "..." if len(op_name) > 25 else op_name
            status_icon = {"completed": "✅", "failed": "❌", "cancelled": "⏹️"}.get(status, "❓")
            
            history_table.add_row(short_name, status_icon)
            
        history_panel = Panel(history_table, title="📜 Recent", border_style="blue")
        
        # Combine queue and history
        sidebar_content = Columns([queue_panel, history_panel], equal=True)
        self.layout["sidebar"].update(sidebar_content)
        
    def _update_footer(self):
        """Update footer with system metrics."""
        current_time = time.time()
        
        # Update system metrics every 2 seconds
        if current_time - self.last_system_update > 2:
            self._collect_system_metrics()
            self.last_system_update = current_time
            
        # Create system metrics table
        metrics_table = Table(show_header=False, box=None, padding=(0, 2))
        metrics_table.add_column("Metric", style="cyan", width=15)
        metrics_table.add_column("Value", style="bold", width=15)
        metrics_table.add_column("Metric", style="cyan", width=15)
        metrics_table.add_column("Value", style="bold", width=15)
        
        # Add metrics in two columns
        metrics = self.system_metrics
        metrics_table.add_row(
            "💻 CPU", f"{metrics.get('cpu_percent', 0):.1f}%",
            "📶 Network ↓", f"{metrics.get('network_recv_mbps', 0):.2f} MB/s"
        )
        metrics_table.add_row(
            "🧠 Memory", f"{metrics.get('memory_mb', 0):.0f} MB",
            "📶 Network ↑", f"{metrics.get('network_send_mbps', 0):.2f} MB/s"
        )
        
        # Database connections (placeholder)
        metrics_table.add_row(
            "🗄️ DB Conn", f"{metrics.get('db_connections', 2)}/20",
            "⏱️ Uptime", format_duration(current_time - self.process.create_time())
        )
        
        footer_panel = Panel(
            metrics_table,
            title="💻 System Resources",
            border_style="blue",
            padding=(0, 1)
        )
        
        self.layout["footer"].update(footer_panel)
        
    def _collect_system_metrics(self):
        """Collect current system metrics."""
        try:
            # CPU and memory
            self.system_metrics['cpu_percent'] = self.process.cpu_percent(interval=0.1)
            memory_info = self.process.memory_info()
            self.system_metrics['memory_mb'] = memory_info.rss / 1024 / 1024
            
            # Network I/O (simplified)
            net_io = psutil.net_io_counters()
            if hasattr(self, '_last_net_io'):
                time_delta = time.time() - self._last_net_time
                if time_delta > 0:
                    bytes_sent_delta = net_io.bytes_sent - self._last_net_io.bytes_sent
                    bytes_recv_delta = net_io.bytes_recv - self._last_net_io.bytes_recv
                    
                    self.system_metrics['network_send_mbps'] = (bytes_sent_delta / time_delta) / (1024 * 1024)
                    self.system_metrics['network_recv_mbps'] = (bytes_recv_delta / time_delta) / (1024 * 1024)
                    
            self._last_net_io = net_io
            self._last_net_time = time.time()
            
            # Database connections (placeholder - would need actual DB connection)
            self.system_metrics['db_connections'] = 2
            
        except Exception:
            # Don't fail if metrics collection fails
            pass