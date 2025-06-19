"""
CLI Commands Package

This package contains all CLI command modules organized by functionality.
"""

# Import available modules
try:
    from .system import app as system_app
except ImportError:
    system_app = None

try:
    from .help import app as help_app
except ImportError:
    help_app = None

try:
    from .ingestion import app as ingestion_app
except ImportError:
    ingestion_app = None

try:
    from .querying import app as querying_app
except ImportError:
    querying_app = None

__all__ = [
    "system_app",
    "help_app",
    "ingestion_app",
    "querying_app"
]