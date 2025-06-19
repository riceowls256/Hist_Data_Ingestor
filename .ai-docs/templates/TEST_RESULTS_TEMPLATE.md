# [FEATURE_NAME] Test Results Document

**Document Status**: NOT_STARTED | IN_PROGRESS | COMPLETE  
**Test Execution Period**: YYYY-MM-DD to YYYY-MM-DD  
**Last Updated**: YYYY-MM-DD  
**Test Lead**: [Name]  
**Related PRD**: [FEATURE_NAME_PRD.md]  
**Related Tech Spec**: [FEATURE_NAME_TECH_SPEC.md]  

## Table of Contents
1. [Test Summary](#test-summary)
2. [Test Environment](#test-environment)
3. [Test Coverage Report](#test-coverage-report)
4. [Unit Test Results](#unit-test-results)
5. [Integration Test Results](#integration-test-results)
6. [End-to-End Test Results](#end-to-end-test-results)
7. [Performance Test Results](#performance-test-results)
8. [Security Test Results](#security-test-results)
9. [Edge Case Testing](#edge-case-testing)
10. [Failed Tests Analysis](#failed-tests-analysis)
11. [Bug Reports](#bug-reports)
12. [Test Artifacts](#test-artifacts)
13. [Sign-off](#sign-off)

## Test Summary

### Overall Results
| Test Type | Total | Passed | Failed | Skipped | Pass Rate |
|-----------|--------|---------|---------|----------|-----------|
| Unit Tests | 0 | 0 | 0 | 0 | 0% |
| Integration Tests | 0 | 0 | 0 | 0 | 0% |
| E2E Tests | 0 | 0 | 0 | 0 | 0% |
| Performance Tests | 0 | 0 | 0 | 0 | 0% |
| Security Tests | 0 | 0 | 0 | 0 | 0% |
| **TOTAL** | **0** | **0** | **0** | **0** | **0%** |

### Test Execution Summary
- **Start Date**: YYYY-MM-DD HH:MM
- **End Date**: YYYY-MM-DD HH:MM
- **Total Duration**: X hours
- **Blocking Issues Found**: 0
- **Critical Bugs**: 0
- **Major Bugs**: 0
- **Minor Bugs**: 0

### Go/No-Go Recommendation
**Status**: NOT_READY | READY_WITH_RISKS | READY  
**Recommendation**: [Clear recommendation based on results]  
**Justification**: [Why this recommendation]

## Test Environment

### Infrastructure
| Component | Version | Configuration | Notes |
|-----------|---------|---------------|--------|
| Operating System | | | |
| Runtime/Language | | | |
| Database | | | |
| Message Queue | | | |
| Cache | | | |

### Test Data
| Dataset | Size | Type | Source |
|---------|------|------|---------|
| [Dataset 1] | [Records] | [Synthetic/Production] | [How generated] |
| [Dataset 2] | [Records] | [Synthetic/Production] | [How generated] |

### Environment Differences from Production
| Aspect | Test Environment | Production | Impact |
|--------|-----------------|------------|--------|
| [Difference] | [Test value] | [Prod value] | [How it affects tests] |

## Test Coverage Report

### Code Coverage Summary
```
PASTE ACTUAL COVERAGE REPORT OUTPUT HERE
Example:
------------------------------------------------------------------------------
File                     Stmts   Miss  Cover   Missing
------------------------------------------------------------------------------
src/main.py                100     10    90%   45-55
src/utils.py                50      5    90%   23, 67-70
src/database.py             75      0   100%
------------------------------------------------------------------------------
TOTAL                      225     15    93%
------------------------------------------------------------------------------
```

### Coverage by Module
| Module | Line Coverage | Branch Coverage | Function Coverage |
|--------|--------------|-----------------|-------------------|
| [Module A] | 0% | 0% | 0% |
| [Module B] | 0% | 0% | 0% |
| **Overall** | **0%** | **0%** | **0%** |

### Uncovered Code Analysis
| File | Lines Not Covered | Reason | Risk |
|------|------------------|---------|------|
| [File] | [Line numbers] | [Why not covered] | HIGH/MED/LOW |

## Unit Test Results

### Test Execution Log
```
PASTE ACTUAL TEST OUTPUT HERE
Example:
$ pytest tests/unit/ -v
========================= test session starts ==========================
platform linux -- Python 3.9.0, pytest-6.2.5, py-1.10.0
collected 45 items

tests/unit/test_auth.py::test_login_success PASSED                [2%]
tests/unit/test_auth.py::test_login_invalid_password PASSED       [4%]
tests/unit/test_auth.py::test_login_user_not_found PASSED         [6%]
...

======================== 45 passed in 2.34s ===========================
```

### Unit Test Summary by Component
| Component | Tests | Passed | Failed | Time |
|-----------|--------|---------|---------|------|
| Authentication | 0 | 0 | 0 | 0s |
| Data Processing | 0 | 0 | 0 | 0s |
| API Handlers | 0 | 0 | 0 | 0s |

### Key Unit Test Scenarios
| Test Case | Description | Result | Duration | Notes |
|-----------|-------------|---------|----------|--------|
| [test_function_1] | [What it tests] | PASS/FAIL | Xms | [Any notes] |
| [test_function_2] | [What it tests] | PASS/FAIL | Xms | [Any notes] |

## Integration Test Results

### API Integration Tests
```
PASTE ACTUAL API TEST OUTPUT HERE
Example:
$ newman run api-tests.json
→ POST /api/v1/login
  ✓ Status code is 200
  ✓ Response time is less than 500ms
  ✓ Response has token
  
→ GET /api/v1/users
  ✓ Status code is 200
  ✓ Response is array
  ✓ Response time is less than 200ms
```

### Database Integration Tests
| Test | Description | Result | Query Time | Notes |
|------|-------------|---------|------------|--------|
| [Connection Test] | [What tested] | PASS/FAIL | Xms | |
| [Write Test] | [What tested] | PASS/FAIL | Xms | |
| [Read Test] | [What tested] | PASS/FAIL | Xms | |

### Service Integration Tests
| Service | Test Scenario | Result | Response Time | Error Details |
|---------|--------------|---------|---------------|---------------|
| [Service A] | [Scenario] | PASS/FAIL | Xms | [If failed] |
| [Service B] | [Scenario] | PASS/FAIL | Xms | [If failed] |

## End-to-End Test Results

### E2E Test Execution
```
PASTE ACTUAL E2E TEST OUTPUT HERE
Example:
$ cypress run
====================================
  (Run Starting)
  
  ┌────────────────────────────────┐
  │ Tests:        12               │
  │ Passing:      11               │
  │ Failing:      1                │
  │ Pending:      0                │
  │ Skipped:      0                │
  │ Screenshots:  1                │
  │ Video:        true             │
  │ Duration:     45 seconds       │
  └────────────────────────────────┘
```

### User Journey Tests
| Journey | Steps | Result | Duration | Screenshots |
|---------|-------|---------|----------|-------------|
| [New User Registration] | 5 | PASS/FAIL | Xs | [Links] |
| [Complete Purchase] | 8 | PASS/FAIL | Xs | [Links] |

### Critical Path Testing
| Path | Description | Result | Issues Found |
|------|-------------|---------|--------------|
| [Happy Path] | [What it covers] | PASS/FAIL | [List issues] |
| [Error Path] | [What it covers] | PASS/FAIL | [List issues] |

## Performance Test Results

### Load Test Results
```
PASTE ACTUAL LOAD TEST OUTPUT HERE
Example:
$ k6 run load-test.js
execution: local
output: -
scenarios: (100.00%) 1 scenario, 100 max VUs, 5m30s max duration
✓ status is 200
✓ response time < 500ms

checks.........................: 100.00% ✓ 45236 ✗ 0
data_received..................: 45 MB   138 kB/s
data_sent......................: 5.4 MB  17 kB/s
http_req_duration..............: avg=126.42ms p(95)=237.81ms
http_reqs......................: 22618   69.44/s
vus............................: 100     min=100 max=100
vus_max........................: 100     min=100 max=100
```

### Performance Metrics vs Requirements
| Metric | Requirement | Actual | Status | Notes |
|--------|------------|---------|---------|--------|
| Response Time (p95) | <200ms | 0ms | NOT_TESTED | |
| Throughput | 1000 RPS | 0 RPS | NOT_TESTED | |
| Error Rate | <0.1% | 0% | NOT_TESTED | |
| CPU Usage | <70% | 0% | NOT_TESTED | |
| Memory Usage | <4GB | 0GB | NOT_TESTED | |

### Stress Test Results
| Load Level | Response Time | Error Rate | CPU | Memory | Notes |
|------------|--------------|------------|-----|---------|--------|
| 100 users | 0ms | 0% | 0% | 0GB | |
| 500 users | 0ms | 0% | 0% | 0GB | |
| 1000 users | 0ms | 0% | 0% | 0GB | |
| Breaking point | N/A | N/A | N/A | N/A | |

## Security Test Results

### Security Scan Summary
```
PASTE ACTUAL SECURITY SCAN OUTPUT HERE
Example:
$ safety check
+==============================================================================+
|                                                                              |
|                               /$$$$$$            /$$                         |
|                              /$$__  $$          | $$                         |
|           /$$$$$$$  /$$$$$$ | $$  \__//$$$$$$  /$$$$$$   /$$   /$$          |
|          /$$_____/ |____  $$| $$$$   /$$__  $$|_  $$_/  | $$  | $$          |
|         |  $$$$$$   /$$$$$$$| $$_/  | $$$$$$$$  | $$    | $$  | $$          |
|          \____  $$ /$$__  $$| $$    | $$_____/  | $$ /$$| $$  | $$          |
|          /$$$$$$$/|  $$$$$$$| $$    |  $$$$$$$  |  $$$$/|  $$$$$$$          |
|         |_______/  \_______/|__/     \_______/   \___/   \____  $$          |
|                                                          /$$  | $$          |
|                                                         |  $$$$$$/          |
|  by pyup.io                                              \______/           |
|                                                                              |
+==============================================================================+
| REPORT                                                                       |
+==============================================================================+
| No known security vulnerabilities found.                                    |
+==============================================================================+
```

### Vulnerability Assessment
| Type | Severity | Count | Details |
|------|----------|--------|---------|
| SQL Injection | HIGH | 0 | |
| XSS | MEDIUM | 0 | |
| CSRF | MEDIUM | 0 | |
| Insecure Dependencies | LOW | 0 | |

### Penetration Test Results
| Test | Method | Result | Risk | Recommendation |
|------|--------|---------|------|----------------|
| [Auth Bypass] | [How tested] | PASS/FAIL | HIGH/MED/LOW | [What to do] |
| [Data Exposure] | [How tested] | PASS/FAIL | HIGH/MED/LOW | [What to do] |

## Edge Case Testing

### Boundary Testing
| Test Case | Input | Expected | Actual | Result |
|-----------|-------|----------|---------|---------|
| [Min value] | [Value] | [Expected] | [Actual] | PASS/FAIL |
| [Max value] | [Value] | [Expected] | [Actual] | PASS/FAIL |
| [Null/Empty] | [Value] | [Expected] | [Actual] | PASS/FAIL |

### Error Handling Tests
```
PASTE ACTUAL ERROR HANDLING TEST OUTPUT
Example:
Testing error scenarios...
✓ Handles network timeout gracefully
✓ Returns appropriate error for invalid input
✓ Maintains data integrity on partial failure
✓ Logs errors with sufficient detail
```

### Concurrency Tests
| Scenario | Concurrent Users | Result | Issues |
|----------|------------------|---------|---------|
| [Simultaneous writes] | 100 | PASS/FAIL | [Race conditions] |
| [Resource locking] | 50 | PASS/FAIL | [Deadlocks] |

## Failed Tests Analysis

### Failed Test Summary
| Test | Type | Failure Reason | Severity | Bug ID |
|------|------|----------------|----------|---------|
| [Test name] | [Unit/Integration/E2E] | [Why it failed] | CRITICAL/HIGH/MED/LOW | [BUG-XXX] |

### Root Cause Analysis
| Bug ID | Root Cause | Impact | Fix Applied | Retested |
|--------|------------|---------|-------------|----------|
| [BUG-001] | [Why it happened] | [What it affects] | YES/NO | PASS/FAIL |

### Flaky Tests
| Test | Flakiness Rate | Reason | Action Taken |
|------|----------------|---------|--------------|
| [Test name] | X% | [Why flaky] | [What was done] |

## Bug Reports

### Bug Summary
| ID | Title | Severity | Status | Assignee |
|----|-------|----------|---------|----------|
| BUG-001 | [Title] | CRITICAL | OPEN/FIXED | [Name] |
| BUG-002 | [Title] | HIGH | OPEN/FIXED | [Name] |

### Critical/Blocking Bugs
| Bug ID | Description | Steps to Reproduce | Impact | Workaround |
|--------|-------------|-------------------|---------|------------|
| [BUG-XXX] | [What's wrong] | 1. Step one<br>2. Step two | [Impact] | [If any] |

### Deferred Bugs
| Bug ID | Reason for Deferral | Risk | Target Fix Date |
|--------|-------------------|------|-----------------|
| [BUG-XXX] | [Why deferred] | [Risk level] | [When] |

## Test Artifacts

### Test Data Files
| File | Purpose | Location | Size |
|------|---------|----------|------|
| [test-data.json] | [What it's for] | [Path/URL] | [Size] |
| [load-test-results.html] | [What it's for] | [Path/URL] | [Size] |

### Screenshots/Videos
| Test | Type | Description | Link |
|------|------|-------------|------|
| [Test name] | Screenshot | [What it shows] | [URL] |
| [E2E test] | Video | [What it shows] | [URL] |

### Log Files
| Log Type | Time Range | Location | Key Findings |
|----------|------------|----------|--------------|
| [Application logs] | [Start-End] | [Path] | [What found] |
| [Error logs] | [Start-End] | [Path] | [What found] |

## Sign-off

### Test Completion Criteria
- [ ] All planned tests executed
- [ ] Test coverage meets requirements (>80%)
- [ ] All critical bugs resolved
- [ ] Performance requirements met
- [ ] Security scan passed
- [ ] Test results documented
- [ ] Artifacts archived

### Approval
| Role | Name | Approved | Date | Comments |
|------|------|----------|------|----------|
| QA Lead | [Name] | YES/NO | YYYY-MM-DD | |
| Dev Lead | [Name] | YES/NO | YYYY-MM-DD | |
| Product Owner | [Name] | YES/NO | YYYY-MM-DD | |

### Post-Testing Action Items
| Action | Owner | Due Date | Status |
|--------|-------|----------|---------|
| [Action item] | [Name] | YYYY-MM-DD | TODO/DONE |

---

**Test Report Generated**: YYYY-MM-DD HH:MM  
**Next Test Cycle**: [If applicable]  
**Archive Location**: [Where this will be stored]