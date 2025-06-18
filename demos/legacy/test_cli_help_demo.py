#!/usr/bin/env python3
"""
CLI Help System Demonstration Script

This script demonstrates the enhanced CLI help features including:
- New help commands (examples, troubleshoot, tips, schemas)
- Enhanced error messages with suggestions
- Dry-run and validate-only modes
- Improved parameter validation
"""

import subprocess
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def run_command(cmd: str, description: str):
    """Run a CLI command and display the output."""
    print(f"\n{'='*80}")
    print(f"DEMO: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*80}\n")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
    except Exception as e:
        print(f"Error running command: {e}")
    
    input("\nPress Enter to continue...")


def main():
    """Run the CLI help demonstration."""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║           CLI Help System Demonstration                           ║
║                                                                   ║
║  This demonstrates the enhanced help features including:          ║
║  - New help commands                                              ║
║  - Better error messages                                          ║
║  - Dry-run and validation modes                                   ║
║  - Interactive troubleshooting                                    ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    demos = [
        # Basic help
        ("python main.py --help", "Main help with improved formatting"),
        
        # New help commands
        ("python main.py examples", "Show all command examples"),
        ("python main.py examples query", "Show query-specific examples"),
        ("python main.py schemas", "Display available data schemas"),
        ("python main.py tips", "Show usage tips and best practices"),
        ("python main.py troubleshoot", "Show common issues and solutions"),
        
        # Enhanced command help
        ("python main.py query --help", "Query command with detailed help"),
        ("python main.py ingest --help", "Ingest command with examples"),
        
        # Error handling with suggestions
        ("python main.py query -s INVALID_SYMBOL --start-date 2024-01-01 --end-date 2024-01-31", 
         "Invalid symbol with helpful error message"),
        
        ("python main.py query -s ES.c.0 --start-date 2024/01/01 --end-date 2024-01-31",
         "Invalid date format with suggestions"),
        
        ("python main.py query -s ES.c.0 --start-date 2024-01-31 --end-date 2024-01-01",
         "Invalid date range with suggestions"),
         
        ("python main.py ingest --api databento",
         "Missing parameters with helpful guidance"),
        
        # Dry-run mode
        ("python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31 --dry-run",
         "Query dry-run mode preview"),
         
        ("python main.py ingest --api databento --job ohlcv_1d --dry-run",
         "Ingest dry-run mode preview"),
        
        # Validate-only mode  
        ("python main.py query -s ES.c.0,NQ.c.0 --start-date 2024-01-01 --end-date 2024-01-31 --validate-only",
         "Parameter validation without execution"),
         
        # Troubleshooting specific errors
        ("python main.py troubleshoot 'database error'",
         "Get help for database issues"),
         
        ("python main.py troubleshoot 'symbol not found'", 
         "Get help for symbol resolution"),
    ]
    
    for cmd, desc in demos:
        run_command(cmd, desc)
    
    print("\n✅ CLI Help System Demonstration Complete!")
    print("\nKey improvements demonstrated:")
    print("  • New help commands for examples, tips, and troubleshooting")
    print("  • Enhanced error messages with actionable suggestions")
    print("  • Dry-run mode to preview operations")
    print("  • Validate-only mode for parameter checking")
    print("  • Context-aware troubleshooting guidance")
    print("  • Better formatting with Rich library")


if __name__ == "__main__":
    main()