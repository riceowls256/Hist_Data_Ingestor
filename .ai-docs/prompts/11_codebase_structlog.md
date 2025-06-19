# Codebase-Wide Logging Practices Review

## Context
I need you to conduct a comprehensive review of our entire codebase to ensure consistent logging practices, specifically that we're using structlog everywhere and following best practices.

## Review Scope

**Review Type**: ARCHITECTURE - Logging Practices Audit
**Focus Area**: Logging implementation across entire codebase
**Target Standard**: structlog everywhere with consistent patterns

## Phase 1: Discovery and Analysis

### 1. Scan Entire Codebase

First, analyze the current state of logging:

```bash
# Find all logging imports
grep -r "import logging" --include="*.py" .
grep -r "from logging import" --include="*.py" .
grep -r "import structlog" --include="*.py" .
grep -r "from structlog import" --include="*.py" .

# Find all logger instantiations
grep -r "getLogger" --include="*.py" .
grep -r "get_logger" --include="*.py" .
grep -r "structlog.get_logger" --include="*.py" .

# Find print statements (shouldn't be in production code)
grep -r "print(" --include="*.py" src/
```

### 2. Create Logging Inventory

Document your findings in a table:

```markdown
| File Path | Current Logging | Logger Instance | Log Statements Count | Issues Found |
|-----------|----------------|-----------------|---------------------|--------------|
| src/api/auth.py | standard logging | logging.getLogger(__name__) | 15 | Not using structlog |
| src/core/database.py | structlog | structlog.get_logger() | 23 | ✓ Correct |
| src/utils/helpers.py | print statements | None | 5 | Using print() |
```

### 3. Pattern Analysis

Identify patterns in the codebase:

- How many files use standard logging vs structlog?
- Are there consistent logger naming conventions?
- What contextual data is being logged?
- Are there any files with NO logging?

## Phase 2: Standards Definition

### Define Structlog Standards

Create our standard patterns:

```python
# Correct pattern - what we want everywhere
import structlog

logger = structlog.get_logger(__name__)

# With context binding
logger = logger.bind(
    service="api",
    version="1.0.0"
)

# Logging examples
logger.info("user_authenticated", user_id=user.id, method="oauth")
logger.error("database_connection_failed", error=str(e), retry_count=3)
```

### Required Logging Patterns

Define what should be logged:

```markdown
## Required Logging Points

### API Endpoints
- Request received (with method, path, user)
- Request completed (with status, duration)
- Errors (with full context)

### Database Operations  
- Query execution (with query type, duration)
- Connection issues
- Transaction boundaries

### Business Logic
- Important state changes
- Decision points
- Validation failures

### External Service Calls
- Request sent (service, endpoint)
- Response received (status, duration)
- Failures and retries
```

## Phase 3: Migration Plan

### For Each File That Needs Updates:

1. **Create Migration Checklist**:
   ```markdown
   ## File: [filepath]
   - [ ] Replace logging import with structlog
   - [ ] Convert logger instantiation
   - [ ] Update all log calls to structured format
   - [ ] Add appropriate context binding
   - [ ] Remove any print statements
   - [ ] Add missing log points
   - [ ] Test changes
   ```

2. **Provide Conversion Examples**:
   ```python
   # BEFORE:
   import logging
   logger = logging.getLogger(__name__)
   logger.info(f"User {user_id} logged in")
   
   # AFTER:
   import structlog
   logger = structlog.get_logger(__name__)
   logger.info("user_login", user_id=user_id)
   ```

## Phase 4: Implementation

### Systematic Updates

For each module/package:

1. Start with core/shared modules
2. Move to API/web layers
3. Update background tasks/workers
4. Fix utility modules

### Testing Each Change

After updating each file:
```bash
# Run tests for the module
pytest tests/unit/[module]/ -v

# Check that logging works
python -c "from src.[module] import *; # verify no import errors"

# Verify log output format
# Run the application and check logs are structured JSON
```

## Phase 5: Configuration

### Create/Update Logging Configuration

```python
# config/logging.py
import structlog

def configure_logging(environment: str = "development"):
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if environment == "production" 
            else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
```

## Phase 6: Validation

### Final Checks

1. **No Standard Logging Remains**:
   ```bash
   # Should return nothing
   grep -r "import logging" --include="*.py" src/
   ```

2. **No Print Statements**:
   ```bash
   # Should return nothing  
   grep -r "print(" --include="*.py" src/
   ```

3. **Consistent Logger Names**:
   ```bash
   # All should use __name__
   grep -r "get_logger()" --include="*.py" src/
   ```

4. **Structured Output Test**:
   ```bash
   # Run app and verify JSON output
   python -m src.main 2>&1 | head -20
   ```

## Deliverables

Create these documents:

### 1. LOGGING_AUDIT_REPORT.md
```markdown
# Logging Audit Report

## Summary
- Files reviewed: X
- Files using standard logging: Y
- Files using structlog: Z
- Files with no logging: N
- Print statements found: P

## Migration Status
[Table of all files and their status]

## Issues Found
[List of problems discovered]

## Recommendations
[Specific improvements needed]
```

### 2. LOGGING_MIGRATION_PLAN.md
With:
- Priority order for updates
- Estimated effort per module
- Risk assessment
- Rollback plan

### 3. LOGGING_STANDARDS.md
Document the agreed patterns for future development

## Success Criteria

- [ ] 100% of files use structlog
- [ ] Zero print statements in src/
- [ ] All loggers use consistent naming
- [ ] Structured JSON output in production
- [ ] Human-readable output in development
- [ ] Appropriate context included in all logs
- [ ] No sensitive data in logs
- [ ] Performance impact measured and acceptable

Begin with Phase 1 discovery and provide the initial inventory of current logging practices.