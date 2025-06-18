# CLI Logging Reduction Implementation

## Overview

This document describes the implementation of CLI logging reduction as specified in `specs/active/CLI_LOGGING_REDUCTION_SPEC.md`. The goal was to create a clean console experience while maintaining comprehensive file logging for debugging.

## Implementation Summary

### Key Changes Made

1. **Separate Log Levels for Console and File**
   - Console: `WARNING` level by default (only important messages)
   - File: `DEBUG` level by default (comprehensive logging)

2. **Enhanced Logger Configuration**
   - Updated `src/utils/custom_logger.py` with dual-handler setup
   - Added `console_level` parameter to `setup_logging()`
   - Clean console formatter without timestamps/logger names

3. **Configuration Updates**
   - Updated `configs/system_config.yaml` to include `console_level`
   - Updated `src/core/config_manager.py` LoggingConfig model
   - Environment variable support for `CONSOLE_LOG_LEVEL`

4. **Convenience Functions**
   - Added `log_status()`, `log_progress()`, `log_user_message()` functions
   - These use WARNING level to ensure console visibility
   - Updated main.py imports to use these functions

## Technical Implementation

### Logger Setup Changes

**Before:**
```python
# Single log level for both console and file
setup_logging(log_level="INFO")
```

**After:**
```python
# Separate levels for console (WARNING) and file (DEBUG)
setup_logging(
    log_level="DEBUG",        # File level - comprehensive
    console_level="WARNING"   # Console level - user-facing only
)
```

### Console Output Filtering

The new system filters messages by importance:

- **Console Shows:** WARNING, ERROR, CRITICAL messages only
- **File Captures:** DEBUG, INFO, WARNING, ERROR, CRITICAL messages

### Message Categories

| Log Level | Console | File | Usage |
|-----------|---------|------|-------|
| DEBUG     | ❌      | ✅   | Internal processing details, API calls, database operations |
| INFO      | ❌      | ✅   | General information, pipeline stages, connection status |
| WARNING   | ✅      | ✅   | User-relevant status updates, progress messages, data issues |
| ERROR     | ✅      | ✅   | Failed operations, rate limits, validation errors |
| CRITICAL  | ✅      | ✅   | System failures, critical errors |

## Usage Examples

### For Developers

```python
from utils.custom_logger import get_logger, log_status, log_progress

# Internal processing (file-only)
logger = get_logger(__name__)
logger.debug("Processing chunk 1 of 100")
logger.info("Database connection established")

# User-facing messages (console + file)
log_status("Starting data ingestion")
log_progress("Processing 50% complete")
logger.warning("Found 3 invalid records")
logger.error("API rate limit exceeded")
```

### Configuration

Environment variables for customization:
```bash
export LOG_LEVEL=DEBUG           # File logging level
export CONSOLE_LOG_LEVEL=WARNING # Console logging level
```

YAML configuration:
```yaml
logging:
  level: "DEBUG"           # File logging level
  console_level: "WARNING" # Console logging level
  file: "logs/app.log"
```

## Testing Results

### Console Output (Clean)
```
Status: Initializing data ingestion pipeline
Progress: Fetching data from Databento API  
Progress: Processing chunk 1 of 15
Found 3 records with missing volume data - using default value 0
Rate limit exceeded - backing off for 5 seconds
Progress: Processing chunk 15 of 15
Status: Data ingestion completed successfully
✅ Ingested 14,997 records for ES.c.0 (2024-01-01 to 2024-01-31)
```

### File Logging (Comprehensive)
```json
{"event": "Loading pipeline configuration from configs/", "logger": "pipeline.orchestrator", "level": "debug", "timestamp": "2025-06-18T01:47:09.626413Z"}
{"event": "Establishing connection to Databento API", "logger": "api.databento", "level": "info", "timestamp": "2025-06-18T01:47:09.626471Z"}
{"event": "Creating database connection pool", "logger": "storage.timescale", "level": "debug", "timestamp": "2025-06-18T01:47:09.626512Z"}
{"event": "Validating record #1: {'symbol': 'ES.c.0', 'open': 4150.25, ...}", "logger": "validation", "level": "debug", "timestamp": "2025-06-18T01:47:09.626675Z"}
...
```

## Benefits Achieved

✅ **Console Cleanliness**: Only essential messages visible to users  
✅ **Comprehensive Debugging**: All technical details preserved in files  
✅ **Developer Experience**: Easy-to-use convenience functions  
✅ **Configurable**: Environment and YAML configuration support  
✅ **Backward Compatible**: Existing logging calls still work  
✅ **Progress Bar Integration**: Clean console won't interfere with progress displays  

## Success Criteria Met

- [x] Console output shows only user-relevant information
- [x] Progress bars display clearly without interruption  
- [x] Critical errors are visible to users
- [x] File logs maintain current level of detail
- [x] No loss of debugging capability
- [x] CLI feels responsive and professional

## Integration Notes

The logging system integrates seamlessly with:
- Rich progress bars in `cli/progress_utils.py`
- Pipeline orchestrator status updates
- API adapter error reporting
- Validation and transformation logging

## Future Enhancements

Potential improvements for future versions:
- Custom log levels (STATUS, PROGRESS) for better categorization
- Log message filtering by component/module
- Real-time log level adjustment via CLI flags
- Integration with external logging services (ELK stack, etc.)

## Files Modified

- `src/utils/custom_logger.py` - Core logging implementation
- `configs/system_config.yaml` - Configuration defaults
- `src/core/config_manager.py` - Configuration model updates
- `src/main.py` - Updated logging initialization

## Testing

Comprehensive testing performed with:
- Unit tests for different log levels
- Realistic data ingestion simulation
- Console output verification
- File logging completeness validation

## Dependency Resolution

During implementation, resolved a missing `psutil` dependency:
- **Issue**: `ModuleNotFoundError: No module named 'psutil'` when importing progress utilities
- **Resolution**: Installed `psutil==7.0.0` (already in requirements.txt)
- **Verification**: CLI commands now work correctly with system monitoring features

## Implementation Status

✅ **COMPLETED** - Moved from `specs/active/` to `specs/completed/`

All success criteria met:
- Console output shows only user-relevant information (WARNING+ level)
- File logs maintain comprehensive debugging details (DEBUG+ level)
- No loss of debugging capability
- Professional, clean CLI experience
- Integration with existing progress bars and UI components

The implementation successfully achieves the goal of clean console output while maintaining comprehensive file logging for debugging and troubleshooting.