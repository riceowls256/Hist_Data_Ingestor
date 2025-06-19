# CLI Enhanced Help System Guide

## Overview

The Historical Data Ingestor CLI has been significantly enhanced with a comprehensive help system designed to make the tool more accessible and user-friendly. This guide covers all the new help features and how to use them effectively.

## New Help Commands

### 1. Interactive Help Menu (`help-menu`)

Launch an interactive, navigable help system with organized categories.

```bash
python main.py help-menu
```

**Features:**
- Navigate through 6 main categories
- Interactive menu system with numbered choices
- Detailed help content for each topic
- Easy navigation with "Back" options

**Categories:**
- 🚀 Getting Started - New user guides
- 📊 Data Ingestion - Learn ingestion techniques
- 🔍 Querying Data - Master data retrieval
- 🎯 Common Workflows - End-to-end examples
- 🔧 Troubleshooting - Solve common issues
- 📚 Reference - Quick lookups

### 2. Quickstart Wizard (`quickstart`)

An interactive setup wizard that guides new users through their first data pipeline.

```bash
python main.py quickstart
```

**What it does:**
1. Checks environment setup (API keys, database)
2. Helps select appropriate data type
3. Assists with symbol selection
4. Suggests sensible date ranges
5. Generates ready-to-use commands

**Perfect for:**
- First-time users
- Testing your setup
- Learning the basics
- Generating example commands

### 3. Workflow Examples (`workflows`)

Complete, real-world workflow examples for common use cases.

```bash
# List all workflows
python main.py workflows

# Show specific workflow
python main.py workflows daily_analysis
python main.py workflows historical_research
python main.py workflows intraday_analysis
```

**Available workflows:**
- **Daily Analysis**: Download and analyze yesterday's market data
- **Historical Research**: Collect data for backtesting
- **Intraday Analysis**: Work with high-frequency trades and quotes

Each workflow includes:
- Step-by-step commands
- Explanations for each step
- Dynamic date calculations
- Best practices

### 4. Symbol Helper (`symbols`)

Discover and search for available trading symbols.

```bash
# Show all symbol categories
python main.py symbols

# Browse specific category
python main.py symbols --category Energy
python main.py symbols --category "Equity Indices"

# Search for symbols
python main.py symbols --search oil
python main.py symbols --search gold
```

**Symbol categories:**
- Equity Indices (ES, NQ, RTY, YM)
- Energy (CL, NG, RB, HO)
- Metals (GC, SI, HG, PL)
- Agriculture (ZC, ZS, ZW, ZL)
- Currencies (6E, 6B, 6J, 6C)
- Fixed Income (ZN, ZB, ZF, ZT)

### 5. Cheat Sheet (`cheatsheet`)

Quick reference card with common commands and shortcuts.

```bash
python main.py cheatsheet
```

**Includes:**
- Common command patterns
- Query shortcuts
- Date format examples
- Symbol format reference
- Pro tips for efficiency

### 6. Enhanced Examples (`examples`)

Comprehensive examples for all commands with practical use cases.

```bash
# Show all examples
python main.py examples

# Command-specific examples
python main.py examples query
python main.py examples ingest
```

## Guided Mode for Commands

Both `ingest` and `query` commands now support an interactive guided mode that walks you through parameter selection.

### Guided Query Mode

```bash
python main.py query --guided
```

**Interactive prompts for:**
- Symbol selection
- Schema type
- Date range
- Output format
- Export options
- Result limits

### Guided Ingest Mode

```bash
python main.py ingest --guided
```

**Interactive prompts for:**
- API selection
- Predefined job or custom config
- Dataset selection
- Schema type
- Symbol entry
- Date range selection

## Enhanced Error Handling

All commands now feature improved error messages with:
- Context-aware suggestions
- Links to relevant help topics
- Example commands that work
- Automatic troubleshooting tips

## Tips for New Users

1. **Start with the quickstart wizard**:
   ```bash
   python main.py quickstart
   ```

2. **Use guided mode for your first commands**:
   ```bash
   python main.py query --guided
   python main.py ingest --guided
   ```

3. **Keep the cheat sheet handy**:
   ```bash
   python main.py cheatsheet
   ```

4. **Explore workflows for complete examples**:
   ```bash
   python main.py workflows
   ```

5. **Use the help menu when stuck**:
   ```bash
   python main.py help-menu
   ```

## Command Comparison: Before vs After

### Before (Complex for new users)
```bash
python main.py ingest --api databento --dataset GLBX.MDP3 --schema ohlcv-1d --symbols ES.c.0,NQ.c.0 --start-date 2024-01-01 --end-date 2024-01-31
```

### After (Multiple helpful options)
```bash
# Option 1: Use quickstart wizard
python main.py quickstart

# Option 2: Use guided mode
python main.py ingest --guided

# Option 3: Use predefined workflow
python main.py workflows daily_analysis

# Option 4: Get help first
python main.py help-menu
```

## Best Practices

1. **Use `--dry-run` to preview commands**:
   ```bash
   python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31 --dry-run
   ```

2. **Validate parameters before execution**:
   ```bash
   python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31 --validate-only
   ```

3. **Start with small date ranges**:
   - OHLCV: Start with a month
   - Trades/TBBO: Start with a single day
   - Use `--limit` for large datasets

4. **Check available symbols**:
   ```bash
   python main.py symbols --category "Equity Indices"
   ```

5. **Follow workflows for complex tasks**:
   ```bash
   python main.py workflows historical_research
   ```

## Troubleshooting

The enhanced troubleshooting system provides targeted help:

```bash
# General troubleshooting
python main.py troubleshoot

# Specific error help
python main.py troubleshoot "database error"
python main.py troubleshoot "symbol not found"
python main.py troubleshoot "API authentication"
```

## Summary

The enhanced CLI help system transforms the user experience by providing:

- **Interactive guidance** through help menus and wizards
- **Practical examples** via workflows and enhanced examples
- **Discovery tools** for symbols and schemas
- **Quick references** through cheat sheets
- **Guided modes** for complex commands
- **Better error handling** with contextual help

These improvements make the Historical Data Ingestor accessible to users of all experience levels, from beginners to advanced users.