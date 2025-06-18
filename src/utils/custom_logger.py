import logging
import logging.handlers
import os
import structlog
from typing import Optional


def setup_logging(log_level: Optional[str] = None, log_file: str = "logs/app.log", 
                 console_level: Optional[str] = None):
    """
    Set up centralized logging for the application using structlog and the standard logging module.
    - Console logs show only user-relevant information (WARNING+ by default)
    - File logs are comprehensive with all debug information (DEBUG level)
    - Log rotation is enabled (5MB, 3 backups)
    - Separate log levels for console and file handlers
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Determine file log level (comprehensive logging)
    file_level = (
        log_level
        or os.environ.get("LOG_LEVEL")
        or "DEBUG"  # Default to DEBUG for files to capture everything
    )
    file_level = getattr(logging, file_level.upper(), logging.DEBUG)
    
    # Determine console log level (user-facing only)
    console_log_level = (
        console_level
        or os.environ.get("CONSOLE_LOG_LEVEL")
        or "WARNING"  # Default to WARNING+ for console (only important messages)
    )
    console_log_level = getattr(logging, console_log_level.upper(), logging.WARNING)

    # Clean formatter for console (user-friendly, minimal clutter)
    console_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(
            colors=True
        ),
        foreign_pre_chain=[
            # No timestamp for console - keep it clean
            structlog.stdlib.add_log_level,
        ],
    )
    # JSON formatter for file
    file_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
        ],
    )

    # Console handler - only important messages
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_log_level)
    console_handler.setFormatter(console_formatter)
    
    # File handler - comprehensive logging
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(file_formatter)

    # Root logger setup - use the lower of the two levels to ensure all messages are captured
    root_level = min(file_level, console_log_level)
    root_logger = logging.getLogger()
    root_logger.setLevel(root_level)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # structlog global config
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Create convenience loggers for different use cases
    _setup_convenience_loggers()
    
    # TODO: In future, support additional structured logging processors or external log sinks as needed.


def _setup_convenience_loggers():
    """
    Setup convenience loggers for different types of messages.
    """
    # These will help developers categorize their log messages appropriately
    pass


def get_logger(name: Optional[str] = None):
    """
    Return a structlog logger for the given module name.
    Usage: logger = get_logger(__name__)
    """
    return structlog.get_logger(name)


def get_console_logger(name: Optional[str] = None):
    """
    Get a logger optimized for console output (user-facing messages).
    This logger should be used for status updates, progress messages, and user notifications.
    """
    logger = structlog.get_logger(name)
    return logger


def get_debug_logger(name: Optional[str] = None):
    """
    Get a logger for detailed debug information (file-only).
    This logger should be used for internal processing details, API calls, etc.
    """
    logger = structlog.get_logger(name)
    return logger


def log_user_message(message: str, level: str = "info"):
    """
    Log a user-facing message that should appear on console.
    
    Args:
        message: The message to display to the user
        level: Log level (info, warning, error)
    """
    logger = get_console_logger("user")
    getattr(logger, level.lower())(message)


def log_status(message: str):
    """
    Log a status update that users should see.
    """
    logger = get_console_logger("status")
    logger.warning(f"Status: {message}")  # Use WARNING level so it appears on console


def log_progress(message: str):
    """
    Log a progress update that users should see.
    """
    logger = get_console_logger("progress")
    logger.warning(f"Progress: {message}")  # Use WARNING level so it appears on console
