# Testing and Validation Prompt

## Context
Use this to ensure comprehensive testing before marking any feature complete.

## Prompt

I need you to perform comprehensive testing and validation for [FEATURE_NAME]. No feature is complete until all tests pass and are documented.

### 1. Pre-Testing Checklist

Confirm these are complete before testing:
- [ ] All code implementation is complete
- [ ] Code has been committed with proper messages
- [ ] Documentation is up to date
- [ ] No TODO comments remain in code
- [ ] All functions have docstrings

### 2. Unit Testing

For EACH module/component:

```bash
# Run unit tests with coverage
pytest tests/unit/[module]/ -v --cov=[module] --cov-report=term-missing

# Paste the FULL output in your test results document
```

Requirements:
- Minimum 80% code coverage
- Test all public functions
- Test error conditions
- Test edge cases
- Test boundary conditions

### 3. Integration Testing

Test all integration points:

```bash
# Run integration tests
pytest tests/integration/ -v

# Test API endpoints
python -m pytest tests/api/ -v

# Test database operations
python -m pytest tests/db/ -v
```

For each integration point, verify:
- [ ] Correct request/response format
- [ ] Error handling works properly
- [ ] Timeouts are handled
- [ ] Retries work as expected

### 4. End-to-End Testing

Create and run E2E test scenarios:

```python
# Example E2E test structure
def test_complete_user_journey():
    # 1. User registration
    # 2. User login  
    # 3. Perform main feature action
    # 4. Verify results
    # 5. Cleanup
```

Document each E2E scenario with:
- Setup required
- Steps performed
- Expected results
- Actual results
- Screenshots/recordings if UI involved

### 5. Performance Testing

Run performance benchmarks:

```bash
# Load testing
locust -f performance/load_test.py --headless -u 100 -r 10 -t 60s

# Memory profiling
python -m memory_profiler performance/memory_test.py

# Response time testing
python performance/response_time_test.py
```

Verify against requirements:
- [ ] Response time < [X]ms (p95)
- [ ] Throughput > [X] requests/second
- [ ] Memory usage < [X]GB
- [ ] CPU usage < [X]%

### 6. Security Testing

Run security scans:

```bash
# Dependency vulnerabilities
safety check

# Code security issues  
bandit -r src/ -f json -o security_report.json

# If API: test for OWASP Top 10
python security/owasp_tests.py
```

### 7. Edge Case Testing

Test these specific scenarios:
- [ ] Empty inputs
- [ ] Null/None values
- [ ] Maximum length inputs
- [ ] Special characters
- [ ] Concurrent operations
- [ ] Network failures
- [ ] Database connection loss

### 8. Regression Testing

Ensure no existing functionality is broken:

```bash
# Run full test suite
pytest tests/ -v

# Compare with baseline
python compare_test_results.py baseline.json current.json
```

### 9. Test Results Documentation

Update your TEST_RESULTS.md with:
- Actual command outputs (not summaries)
- Coverage reports
- Performance metrics
- Failed test analysis
- Bug reports for any failures

### 10. Final Validation

Before marking complete:
- [ ] All tests passing
- [ ] Coverage meets requirements
- [ ] Performance acceptable
- [ ] No security vulnerabilities
- [ ] Documentation complete
- [ ] Code review items addressed

Only after ALL tests pass and are documented can you update the task status to COMPLETE.
