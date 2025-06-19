# Structlog Migration Documentation

**Document Status**: DRAFT  
**Version**: 1.0  
**Last Updated**: 2025-06-19  
**Documentation Lead**: AI Agent  
**Related PRD**: [STRUCTLOG_MIGRATION_PRD.md]  
**Related Tech Spec**: [STRUCTLOG_MIGRATION_TECH_SPEC.md]  

## Table of Contents
1. [Documentation Overview](#documentation-overview)
2. [User Documentation](#user-documentation)
3. [API Documentation](#api-documentation)
4. [Developer Documentation](#developer-documentation)
5. [Operations Documentation](#operations-documentation)
6. [Troubleshooting Guide](#troubleshooting-guide)
7. [FAQ](#faq)
8. [Glossary](#glossary)
9. [Documentation Maintenance](#documentation-maintenance)

## Documentation Overview

### Purpose
This documentation provides comprehensive guidance for using, implementing, and maintaining structured logging with structlog throughout the Historical Data Ingestor application. It covers developer guidelines, operational procedures, and troubleshooting information.

### Documentation Types
| Type | Audience | Location | Status |
|------|----------|----------|---------|
| Logging Standards Guide | Developers | This document | DRAFT |
| API Reference | Developers | This document | DRAFT |
| Operations Guide | DevOps/SRE | This document | DRAFT |
| Troubleshooting Guide | All teams | This document | DRAFT |

### Related Resources
- [structlog documentation](https://www.structlog.org/)
- [Python logging best practices](https://docs.python.org/3/howto/logging.html)
- [JSON logging standards](https://jsonlines.org/)

## User Documentation

### Getting Started Guide

#### Prerequisites
- Python 3.11+ environment
- Historical Data Ingestor application installed
- Basic understanding of logging concepts

#### Quick Start

1. **Understanding Log Levels**:
   ```
   DEBUG    - Detailed information for diagnosing problems
   INFO     - General informational messages
   WARNING  - Warning messages for potentially harmful situations
   ERROR    - Error messages for serious problems
   CRITICAL - Critical messages for very serious errors
   ```

2. **Viewing Logs in Development**:
   ```bash
   # Logs appear in console with color coding
   python main.py status
   # Example output:
   2025-06-19 10:30:45 [info     ] application_started    service=hist_data_ingestor version=2.0.0
   ```

3. **Viewing Logs in Production**:
   ```bash
   # JSON formatted logs in log files
   tail -f logs/app.log | jq '.'
   # Pretty-printed JSON output
   ```

### Configuration Guide

#### Basic Configuration
```yaml
# configs/system_config.yaml
logging:
  level: INFO                    # Minimum log level
  format: json                   # json or console
  file_path: logs/app.log       # Log file location
  max_size_mb: 100              # Max file size before rotation
  backup_count: 3               # Number of backup files
  
  # Environment-specific settings
  environments:
    development:
      format: console           # Human-readable
      level: DEBUG              # More verbose
      colors: true              # Colored output
    
    production:
      format: json              # Machine-readable
      level: INFO               # Less verbose
      colors: false             # No colors
```

#### Environment Variables
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| LOG_LEVEL | No | INFO | Minimum log level |
| LOG_FORMAT | No | Auto-detect | json or console |
| ENVIRONMENT | No | development | Environment name |
| LOG_FILE | No | logs/app.log | Log file path |

### Log Output Examples

#### Development Console Output
```
2025-06-19 10:30:45 [info     ] ingestion_started      symbol=ES.c.0 start_date=2024-01-01 component=ingestion
2025-06-19 10:30:47 [debug    ] api_request            endpoint=/historical method=GET status=200 duration_ms=1234
2025-06-19 10:30:48 [warning  ] rate_limit_approaching current=85 limit=100 reset_in=300
2025-06-19 10:30:50 [error    ] validation_failed      field=price reason=negative_value record_id=12345
```

#### Production JSON Output
```json
{
  "timestamp": "2025-06-19T10:30:45.123456Z",
  "level": "info",
  "event": "ingestion_started",
  "logger": "src.ingestion.databento_adapter",
  "symbol": "ES.c.0",
  "start_date": "2024-01-01",
  "component": "ingestion",
  "service": "hist_data_ingestor",
  "version": "2.0.0",
  "environment": "production"
}
```

## API Documentation

### Logging API Overview
The application uses structlog for all logging operations. Here's how to use it effectively:

### Basic Usage

```python
import structlog

# Get a logger for your module
logger = structlog.get_logger(__name__)

# Basic logging
logger.info("operation_completed", duration_seconds=1.23)
logger.warning("threshold_exceeded", current=95, limit=100)
logger.error("connection_failed", host="api.example.com", error="timeout")
```

### Advanced Usage

#### Context Binding
```python
# Bind context that persists for all subsequent logs
log = logger.bind(user_id="user123", request_id="req456")
log.info("request_started", path="/api/data")
log.info("request_completed", status=200)  # user_id and request_id included
```

#### Conditional Logging
```python
# Only compute expensive operations if needed
if logger.isEnabledFor(logging.DEBUG):
    debug_info = compute_expensive_debug_info()
    logger.debug("detailed_state", **debug_info)
```

#### Exception Logging
```python
try:
    risky_operation()
except Exception as e:
    logger.exception("operation_failed", operation="risky_operation")
    # Automatically includes stack trace
```

### Logging Standards

#### Event Naming Conventions
| Pattern | Example | Use Case |
|---------|---------|----------|
| `<noun>_<past_tense_verb>` | `user_authenticated` | Completed actions |
| `<noun>_<verb>ing` | `data_processing` | Ongoing actions |
| `<noun>_failed` | `payment_failed` | Failed operations |
| `<noun>_<state>` | `connection_ready` | State changes |

#### Required Fields by Log Level
| Level | Required Fields | Example |
|-------|----------------|---------|
| DEBUG | event, details | `logger.debug("cache_lookup", key=key, found=True)` |
| INFO | event, key metrics | `logger.info("api_call", endpoint=url, duration_ms=123)` |
| WARNING | event, threshold, current | `logger.warning("memory_high", used_mb=1800, limit_mb=2000)` |
| ERROR | event, error, context | `logger.error("db_error", error=str(e), query=query)` |

### Module-Specific Logging Patterns

#### Data Ingestion
```python
# Start of ingestion
logger.info("ingestion_started", 
    symbol=symbol,
    dataset=dataset,
    date_range=f"{start_date} to {end_date}"
)

# Progress updates
logger.info("ingestion_progress",
    symbol=symbol,
    records_processed=count,
    percentage_complete=pct
)

# Completion
logger.info("ingestion_completed",
    symbol=symbol,
    total_records=total,
    duration_seconds=duration,
    success_rate=rate
)
```

#### API Operations
```python
# API request
logger.info("api_request",
    method=method,
    endpoint=endpoint,
    params=sanitized_params  # Remove sensitive data
)

# API response
logger.info("api_response",
    status_code=response.status_code,
    duration_ms=duration,
    response_size=len(response.content)
)
```

#### Database Operations
```python
# Query execution
logger.debug("query_executed",
    query_type="SELECT",
    table="ohlcv_data",
    duration_ms=duration
)

# Connection management
logger.info("connection_created",
    pool_size=pool.size(),
    active_connections=pool.active_count()
)
```

## Developer Documentation

### Setting Up Logging in New Modules

#### Step 1: Import and Initialize
```python
# At the top of your module
import structlog

# Create module-level logger
logger = structlog.get_logger(__name__)
```

#### Step 2: Add Contextual Logging
```python
class YourService:
    def __init__(self, service_name: str):
        # Bind service-specific context
        self.logger = logger.bind(
            service=service_name,
            component="your_component"
        )
    
    def process(self, item_id: str):
        # Bind operation-specific context
        log = self.logger.bind(item_id=item_id)
        log.info("processing_started")
        
        try:
            # Your logic here
            result = self._do_work(item_id)
            log.info("processing_completed", result=result)
        except Exception as e:
            log.error("processing_failed", error=str(e))
            raise
```

### Testing with Logging

#### Capturing Logs in Tests
```python
import structlog
from structlog.testing import capture_logs

def test_your_function():
    # Capture logs during test
    with capture_logs() as cap_logs:
        your_function()
    
    # Verify logs
    assert len(cap_logs) == 2
    assert cap_logs[0]["event"] == "processing_started"
    assert cap_logs[1]["event"] == "processing_completed"
    assert cap_logs[1]["result"] == expected_result
```

#### Testing Log Output Format
```python
def test_json_output():
    # Configure for JSON
    configure_structlog(environment="production")
    
    # Capture stdout
    with capture_stdout() as output:
        logger.info("test_event", value=123)
    
    # Verify JSON format
    log_line = json.loads(output.getvalue())
    assert log_line["event"] == "test_event"
    assert log_line["value"] == 123
```

### Performance Best Practices

1. **Avoid String Formatting in Log Calls**
   ```python
   # Bad - string always formatted
   logger.info(f"Processing {len(items)} items")
   
   # Good - structured data
   logger.info("processing_items", count=len(items))
   ```

2. **Use Lazy Evaluation for Expensive Operations**
   ```python
   # Bad - always computed
   logger.debug("state_dump", state=expensive_serialization())
   
   # Good - only computed if needed
   logger.debug("state_dump", state=lambda: expensive_serialization())
   ```

3. **Batch Log Operations in Loops**
   ```python
   # Bad - log every item
   for item in large_list:
       logger.debug("processing_item", item=item)
   
   # Good - periodic updates
   for i, item in enumerate(large_list):
       if i % 1000 == 0:
           logger.info("batch_progress", processed=i, total=len(large_list))
   ```

### Security Considerations

#### Sensitive Data Masking
```python
# Automatic masking for common patterns
def mask_sensitive_fields(logger, method_name, event_dict):
    """Processor to mask sensitive data."""
    sensitive_keys = ["password", "token", "api_key", "secret"]
    
    for key in list(event_dict.keys()):
        if any(s in key.lower() for s in sensitive_keys):
            event_dict[key] = "***REDACTED***"
    
    return event_dict

# Add to processor chain
structlog.configure(
    processors=[
        # ... other processors ...
        mask_sensitive_fields,
        # ... renderers ...
    ]
)
```

#### Safe Logging Practices
```python
# Never log sensitive data directly
# Bad
logger.info("user_login", username=username, password=password)

# Good
logger.info("user_login", username=username, auth_method="password")

# Sanitize user input
# Bad
logger.info("search_query", query=user_input)

# Good
logger.info("search_query", query=sanitize(user_input), query_length=len(user_input))
```

## Operations Documentation

### Log Management

#### Log Rotation Configuration
```yaml
# Automatic rotation settings
logging:
  rotation:
    max_bytes: 104857600  # 100MB
    backup_count: 5       # Keep 5 old files
    compress: true        # Gzip old files
```

#### Manual Log Rotation
```bash
# Force rotation
mv logs/app.log logs/app.log.$(date +%Y%m%d)
touch logs/app.log
# Restart application to pick up new file

# Compress old logs
gzip logs/app.log.2025*
```

### Log Analysis

#### Common Queries

1. **Find all errors in the last hour**:
   ```bash
   jq 'select(.level == "error" and .timestamp > (now - 3600 | todate))' logs/app.log
   ```

2. **Count events by type**:
   ```bash
   jq -r '.event' logs/app.log | sort | uniq -c | sort -nr
   ```

3. **Track specific request**:
   ```bash
   jq 'select(.request_id == "req123")' logs/app.log
   ```

4. **Performance analysis**:
   ```bash
   jq 'select(.event == "api_response") | .duration_ms' logs/app.log | \
     awk '{sum+=$1; count++} END {print "Avg:", sum/count, "ms"}'
   ```

### Monitoring Integration

#### Prometheus Metrics from Logs
```python
# Export metrics based on logs
from prometheus_client import Counter, Histogram

error_counter = Counter('app_errors_total', 'Total errors logged')
request_duration = Histogram('request_duration_seconds', 'Request duration')

def metrics_processor(logger, method_name, event_dict):
    """Extract metrics from log events."""
    if event_dict.get("level") == "error":
        error_counter.inc()
    
    if event_dict.get("event") == "request_completed":
        duration = event_dict.get("duration_seconds", 0)
        request_duration.observe(duration)
    
    return event_dict
```

#### Log Aggregation Setup
```yaml
# Filebeat configuration for shipping logs
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/app/*.log
  json.keys_under_root: true
  json.add_error_key: true
  
output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "app-logs-%{+yyyy.MM.dd}"
```

## Troubleshooting Guide

### Common Issues

#### Issue: No Logs Appearing
**Symptoms**: 
- Application runs but no logs visible
- Log files empty

**Diagnosis**:
```bash
# Check log level
echo $LOG_LEVEL

# Verify logger initialization
grep -r "get_logger" src/ | head -5

# Check file permissions
ls -la logs/
```

**Solutions**:
1. Ensure LOG_LEVEL is not set too high (e.g., CRITICAL)
2. Verify structlog is configured at startup
3. Check file permissions on log directory
4. Verify logger is initialized correctly

#### Issue: Logs Not in Expected Format
**Symptoms**:
- JSON expected but getting console format
- Colors in production logs

**Diagnosis**:
```python
# Check current configuration
import os
print(f"ENVIRONMENT: {os.getenv('ENVIRONMENT')}")
print(f"LOG_FORMAT: {os.getenv('LOG_FORMAT')}")
```

**Solutions**:
1. Set ENVIRONMENT=production for JSON logs
2. Explicitly set LOG_FORMAT=json
3. Check configuration loading order

#### Issue: High Memory Usage from Logging
**Symptoms**:
- Memory grows continuously
- OOM errors related to logging

**Diagnosis**:
```bash
# Monitor logger objects
import gc
import structlog

loggers = [obj for obj in gc.get_objects() 
           if isinstance(obj, structlog.BoundLogger)]
print(f"Active loggers: {len(loggers)}")
```

**Solutions**:
1. Don't create loggers in loops
2. Use module-level loggers
3. Clear context when done:
   ```python
   structlog.contextvars.clear_contextvars()
   ```

#### Issue: Sensitive Data in Logs
**Symptoms**:
- Passwords, tokens, or PII visible in logs
- Security scan failures

**Diagnosis**:
```bash
# Search for common sensitive patterns
grep -E "(password|token|api_key|secret)" logs/app.log
```

**Solutions**:
1. Add sensitive data processor
2. Review all log statements
3. Implement field masking
4. Add pre-commit hooks to check

### Performance Optimization

#### Reducing Logging Overhead
1. **Use Appropriate Log Levels**:
   ```python
   # Production
   LOG_LEVEL=INFO
   
   # Development only
   LOG_LEVEL=DEBUG
   ```

2. **Conditional Debug Logging**:
   ```python
   if logger.isEnabledFor(logging.DEBUG):
       expensive_debug_info = generate_debug_data()
       logger.debug("debug_info", **expensive_debug_info)
   ```

3. **Async Logging for High Volume**:
   ```python
   # Use async handler
   from concurrent.futures import ThreadPoolExecutor
   
   executor = ThreadPoolExecutor(max_workers=1)
   
   def async_processor(logger, method_name, event_dict):
       executor.submit(write_to_disk, event_dict)
       return event_dict
   ```

## FAQ

### General Questions

**Q: What is structlog and why are we using it?**  
A: structlog is a structured logging library that makes it easier to produce consistent, machine-readable logs. We use it for better log analysis, debugging, and monitoring capabilities.

**Q: How do I switch between JSON and console output?**  
A: Set the ENVIRONMENT variable:
- `ENVIRONMENT=production` for JSON output
- `ENVIRONMENT=development` for console output
- Or set `LOG_FORMAT=json` or `LOG_FORMAT=console` explicitly

**Q: Can I still use print() statements?**  
A: No, print() statements should not be used in production code. Always use the logger instead. During development, use `logger.debug()` for temporary output.

### Technical Questions

**Q: How do I log exceptions with stack traces?**  
A: Use `logger.exception()`:
```python
try:
    risky_operation()
except Exception:
    logger.exception("operation_failed")  # Includes full stack trace
```

**Q: How do I add request IDs to all logs in a request?**  
A: Use context binding:
```python
logger = structlog.get_logger()
request_logger = logger.bind(request_id=generate_request_id())
# Use request_logger for all operations in this request
```

**Q: How much overhead does structlog add?**  
A: Typically less than 1ms per log statement. For performance-critical paths, use conditional logging or higher log levels.

### Troubleshooting Questions

**Q: Why are my logs not showing in tests?**  
A: Use structlog's test utilities:
```python
from structlog.testing import capture_logs

with capture_logs() as cap_logs:
    your_function()
assert cap_logs[0]["event"] == "expected_event"
```

**Q: How do I debug logging configuration?**  
A: Check the current configuration:
```python
import structlog
print(structlog.get_config())
```

## Glossary

| Term | Definition |
|------|------------|
| Structured Logging | Logging data in a consistent, machine-readable format (usually JSON) |
| Event | The name of what happened (e.g., "user_login", "file_uploaded") |
| Context | Additional data attached to log entries (e.g., user_id, request_id) |
| Processor | A function that transforms log events before output |
| Renderer | A function that formats the final log output |
| Log Level | The severity/importance of a log message (DEBUG, INFO, WARNING, ERROR) |
| Context Binding | Attaching persistent data to a logger instance |
| Log Rotation | Automatically creating new log files when size/time limits are reached |

## Documentation Maintenance

### Update Schedule
- **Logging Standards**: Review quarterly
- **API Documentation**: Update with each feature
- **Operations Guide**: Review monthly
- **Troubleshooting**: Update as issues discovered

### Documentation Standards
- Use clear, concise language
- Include code examples for everything
- Test all examples before documenting
- Keep troubleshooting section current
- Version all major changes

### Feedback and Contributions
- Submit issues: Create tickets for documentation gaps
- Submit improvements: PRs welcome for doc updates
- Questions: Reach out to the platform team

---

**Documentation Version**: 1.0  
**Last Review**: 2025-06-19  
**Next Review**: 2025-07-19  
**Feedback**: platform-team@example.com