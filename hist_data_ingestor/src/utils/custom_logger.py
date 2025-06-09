import logging
import logging.handlers
import os
import structlog
from typing import Optional

def setup_logging(log_level: Optional[str] = None, log_file: str = "logs/app.log"):
    """
    Set up centralized logging for the application using structlog and the standard logging module.
    - Console logs are pretty-printed for humans.
    - File logs are JSON-formatted for machine parsing.
    - Log rotation is enabled (5MB, 3 backups).
    - Log level is configurable via argument, environment variable, or config manager.
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Determine log level
    level = (
        log_level
        or os.environ.get("LOG_LEVEL")
        or "INFO"
    )
    level = getattr(logging, level.upper(), logging.INFO)

    # Standard formatter for console
    console_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(),
        foreign_pre_chain=[
            structlog.processors.TimeStamper(fmt="iso"),
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

    # Handlers
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(file_formatter)

    # Root logger setup
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
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

    # TODO: In future, support additional structured logging processors or external log sinks as needed.

def get_logger(name: Optional[str] = None):
    """
    Return a structlog logger for the given module name.
    Usage: logger = get_logger(__name__)
    """
    return structlog.get_logger(name)
