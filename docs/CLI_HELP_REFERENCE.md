# CLI Help System Reference

## New Help Commands

### `examples` - Show practical usage examples
```bash
# Show all examples
python main.py examples

# Show command-specific examples
python main.py examples query
python main.py examples ingest
```

### `troubleshoot` - Get help for errors
```bash
# Show all common issues
python main.py troubleshoot

# Get help for specific errors
python main.py troubleshoot "database error"
python main.py troubleshoot "symbol not found"
python main.py troubleshoot "API authentication"
```

### `tips` - Display best practices
```bash
# Show all tips
python main.py tips

# Show category-specific tips
python main.py tips performance
python main.py tips troubleshooting
python main.py tips efficiency
```

### `schemas` - View data schema information
```bash
# Display all available schemas with descriptions
python main.py schemas
```

## Enhanced Command Features

### Query Command Enhancements

#### Dry-Run Mode
Preview what the query will do without executing:
```bash
python main.py query -s ES.c.0 \
    --start-date 2024-01-01 --end-date 2024-01-31 \
    --dry-run
```

#### Validate-Only Mode
Check parameters without running the query:
```bash
python main.py query -s ES.c.0,NQ.c.0 \
    --start-date 2024-01-01 --end-date 2024-01-31 \
    --validate-only
```

### Ingest Command Enhancements

#### Dry-Run Mode
Preview ingestion without execution:
```bash
python main.py ingest --api databento --job ohlcv_1d --dry-run
```

#### Enhanced Help
More detailed parameter descriptions:
```bash
python main.py ingest --help
```

## Error Message Improvements

### Symbol Validation
- Shows available symbols when invalid symbol is used
- Provides format examples (ES.c.0, CL.FUT)
- Links to documentation

### Date Validation
- Shows correct format (YYYY-MM-DD)
- Provides example dates
- Suggests valid date ranges
- Validates start < end date

### Missing Parameters
- Shows which parameters are required
- Provides working examples
- Explains both job and custom modes

### Database Errors
- Links to troubleshooting steps
- Shows how to check connectivity
- Provides docker commands

## Interactive Features

### Confirmation Prompts
- Shows configuration before execution
- Allows review of parameters
- Can be skipped with `--force`

### Progress Indicators
- Real-time progress bars
- Execution time tracking
- Record count updates
- Memory usage (where applicable)

### Configuration Display
- Shows all parameters in a table
- Highlights overrides
- Indicates dry-run mode

## Best Practices

### Use Examples Command
Before running a new command, check examples:
```bash
python main.py examples query
```

### Validate Complex Queries
For large or complex operations, validate first:
```bash
python main.py query --validate-only ...
```

### Preview with Dry-Run
Always preview destructive or expensive operations:
```bash
python main.py ingest --dry-run ...
```

### Check Status First
Before queries or ingestion:
```bash
python main.py status
```

### Get Help for Errors
When you encounter an error:
```bash
python main.py troubleshoot "error message"
```

## Quick Command Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `examples` | Show usage examples | `python main.py examples query` |
| `troubleshoot` | Get error help | `python main.py troubleshoot` |
| `tips` | Best practices | `python main.py tips performance` |
| `schemas` | Data types info | `python main.py schemas` |
| `--dry-run` | Preview operation | `query ... --dry-run` |
| `--validate-only` | Check parameters | `query ... --validate-only` |
| `--help` | Command help | `query --help` |

## Common Workflows

### First Time Setup
1. `python main.py status` - Check system
2. `python main.py schemas` - Understand data types
3. `python main.py examples` - Learn commands

### Before Querying
1. `python main.py status` - Verify connectivity
2. `python main.py query ... --validate-only` - Check parameters
3. `python main.py query ... --dry-run` - Preview
4. `python main.py query ...` - Execute

### Troubleshooting Issues
1. Copy error message
2. `python main.py troubleshoot "error"` - Get specific help
3. `python main.py status` - Check system health
4. Check logs if needed

### Learning the System
1. `python main.py examples` - See all examples
2. `python main.py tips` - Learn best practices
3. `python main.py schemas` - Understand data
4. Try commands with `--dry-run` first