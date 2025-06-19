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

__all__ = [
    "system_app",
    "help_app"
]