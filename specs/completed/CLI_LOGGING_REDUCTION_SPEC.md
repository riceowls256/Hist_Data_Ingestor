# CLI Logging Reduction Specification

## Problem Statement

The CLI currently streams excessive logging information to the console, making it difficult for users to focus on important status updates and progress. All detailed logging should be relegated to log files while the console should only show:
- Progress bars
- Status updates  
- Critical errors
- User-relevant information

## Current State

- Console output is cluttered with detailed log messages
- Users cannot easily see progress or important status updates
- All logging appears to go to both console and files without proper filtering

## Desired Outcome

### Console Output Should Include:
- Clean progress bars showing ingestion/processing progress
- High-level status messages (e.g., "Starting ingestion...", "Completed successfully")
- Critical errors that require user attention
- Summary statistics (records processed, success rates, etc.)

### Console Output Should NOT Include:
- Debug-level logging
- Detailed internal processing logs
- API request/response details
- Database operation logs
- Transformation step details

### File Logging Should Remain:
- All current detailed logging preserved in log files
- Debug information for troubleshooting
- Complete audit trail of operations

## Technical Requirements

### 1. Separate Console and File Log Levels
- Console handler: INFO level or higher, with selective filtering
- File handler: DEBUG level (maintain current detailed logging)

### 2. Custom Console Formatter
- Clean, user-friendly message formatting
- Remove technical details (timestamps, logger names, etc.) from console
- Keep structured logging for files

### 3. Progress Bar Integration  
- Integrate with existing progress bar implementations
- Ensure progress bars aren't interrupted by log messages
- Show meaningful progress indicators for long-running operations

### 4. Log Message Classification
- Categorize log messages as console-worthy vs file-only
- Use appropriate logging levels and custom filters
- Consider adding custom log levels if needed (e.g., STATUS, PROGRESS)

## Implementation Strategy

### Phase 1: Logging Configuration Refactor
- Identify current logging setup in the codebase
- Separate console and file handlers with different configurations
- Implement custom filters for console output

### Phase 2: Message Categorization
- Review existing log messages and categorize them
- Update log calls to use appropriate levels
- Add user-friendly status messages where needed

### Phase 3: Progress Bar Enhancement
- Ensure progress bars work cleanly with new logging setup
- Add progress indicators for operations that lack them
- Prevent log message interference with progress display

### Phase 4: Testing and Validation
- Test CLI output with various operations
- Verify file logging remains comprehensive
- Ensure critical errors still appear on console

## Success Criteria

- [ ] Console output shows only user-relevant information
- [ ] Progress bars display clearly without interruption
- [ ] Critical errors are visible to users
- [ ] File logs maintain current level of detail
- [ ] No loss of debugging capability
- [ ] CLI feels responsive and professional

## Files Likely to be Modified

- Logging configuration files
- CLI entry points (main.py, cli modules)
- Pipeline orchestrator (for progress reporting)
- Utility modules handling logging setup

## Testing Requirements

- Verify console output cleanliness across all CLI commands
- Confirm file logging completeness is preserved
- Test error scenarios to ensure critical messages appear
- Validate progress bar functionality during long operations

## Risks and Considerations

- Risk of hiding important error information from users
- Need to balance cleanliness with informativeness
- Ensure debugging capability isn't compromised
- Backward compatibility with existing log analysis tools