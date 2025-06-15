#!/usr/bin/env python3
"""
Root entry point for the Historical Data Ingestor application.

This script serves as the main entry point and delegates to the actual CLI
implementation in src/main.py.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    from main import app
    app() 