# AI Agent Implementation Checklist

**Purpose**: This checklist ensures AI agents complete all required tasks with proper verification and documentation. Each checkbox must be completed with evidence.

## 🚦 Pre-Implementation Phase

### Document Preparation
- [ ] **Create all 4 required documents**
  - [ ] `FEATURE_NAME_PRD.md` created in `/active/`
  - [ ] `FEATURE_NAME_TECH_SPEC.md` created in `/active/`
  - [ ] `FEATURE_NAME_TEST_RESULTS.md` created in `/active/`
  - [ ] `FEATURE_NAME_DOCS.md` created in `/active/`
- [ ] **Link all documents together** - Each document references the others
- [ ] **Set document status to "DRAFT"** in all headers

### Code Standards Verification
- [ ] **Query context7 MCP server** for:
  - [ ] Current coding conventions in the project
  - [ ] Naming standards for files, functions, and variables
  - [ ] Import organization patterns
  - [ ] Error handling patterns
  - [ ] Logging standards
  - [ ] Test file naming and structure conventions
- [ ] **Document findings** in Tech Spec under "Code Standards" section

### Requirements Analysis
- [ ] **Read PRD thoroughly** - Understand all requirements
- [ ] **Identify all affected services** - List in Tech Spec
- [ ] **Create detailed task breakdown** - Subtasks for each requirement
- [ ] **Estimate complexity** - Mark each task as SIMPLE/MEDIUM/COMPLEX
- [ ] **Flag unclear requirements** - Ask for clarification before proceeding

### Risk Assessment
- [ ] **Complete risk analysis** in Tech Spec:
  - [ ] Technical risks identified
  - [ ] Service dependencies mapped
  - [ ] Performance impact estimated
  - [ ] Security concerns noted
  - [ ] Rollback strategy defined
- [ ] **Get risk assessment reviewed** before starting implementation

## 💻 Implementation Phase

### Code Development
- [ ] **Follow TDD approach**:
  - [ ] Write test first
  - [ ] Write minimal code to pass test
  - [ ] Refactor while keeping tests green
  - [ ] Paste test output in test results document
- [ ] **Document as you code**:
  - [ ] Add docstrings to ALL functions
  - [ ] Comment complex logic
  - [ ] Update README if needed
  - [ ] Add inline TODO comments for future work

### Code Quality Checks
- [ ] **Before EVERY commit**:
  - [ ] Run linter and paste output
  - [ ] Run formatter and verify changes
  - [ ] Run type checker (if applicable)
  - [ ] Check code coverage is >80%
  - [ ] Verify no new security warnings
- [ ] **Use context7 MCP** to verify:
  - [ ] Import patterns match project standards
  - [ ] Function signatures follow conventions
  - [ ] Error messages follow project format

### Testing Requirements
- [ ] **Unit Tests**:
  - [ ] Test each public function
  - [ ] Test error conditions
  - [ ] Test edge cases
  - [ ] Paste actual test output in test results document
- [ ] **Integration Tests**:
  - [ ] Test API endpoints
  - [ ] Test database operations
  - [ ] Test external service calls
  - [ ] Mock external dependencies appropriately
- [ ] **Performance Tests**:
  - [ ] Baseline performance before changes
  - [ ] Test with expected load
  - [ ] Test with 10x expected load
  - [ ] Document all metrics

### Documentation Updates
- [ ] **For EVERY code change**:
  - [ ] Update relevant documentation
  - [ ] Add/update code examples
  - [ ] Update configuration samples
  - [ ] Document new environment variables
  - [ ] Update troubleshooting guide with potential issues

## 🧪 Verification Phase

### Test Execution
- [ ] **Run complete test suite**:
  ```bash
  # Must paste this EXACT output in test results document
  pytest -v --cov=. --cov-report=term-missing
  ```
- [ ] **Run security scan**:
  ```bash
  # Must paste output
  safety check
  bandit -r src/
  ```
- [ ] **Run performance tests**:
  ```bash
  # Must paste output with metrics
  python performance_test.py
  ```
- [ ] **Verify in development environment**:
  - [ ] Deploy to dev
  - [ ] Run smoke tests
  - [ ] Take screenshots of working features
  - [ ] Record video of user journey (if UI changes)

### Evidence Collection
- [ ] **Update Test Results Document** with:
  - [ ] Actual command outputs (not summaries)
  - [ ] Coverage report showing >80%
  - [ ] Performance metrics vs. requirements
  - [ ] Screenshots/videos of working features
  - [ ] List of any failed tests with explanations
- [ ] **Create demo artifacts**:
  - [ ] Working demo script
  - [ ] Sample input/output data
  - [ ] API request/response examples

### Quality Gates Verification
- [ ] **Gate 1: Planning → Development**
  - [ ] All documents created and linked
  - [ ] Tech spec reviewed and approved
  - [ ] Test plan covers all scenarios
  - [ ] No unanswered questions
- [ ] **Gate 2: Development → Testing**
  - [ ] All code complete
  - [ ] Unit tests passing with >80% coverage
  - [ ] Code review comments addressed
  - [ ] Documentation draft complete
- [ ] **Gate 3: Testing → Deployment**
  - [ ] All tests passing
  - [ ] Performance requirements met
  - [ ] Security scan clean
  - [ ] Documentation finalized

## 📋 Completion Phase

### Final Verification
- [ ] **Code Quality Final Check**:
  - [ ] No TODO comments remaining
  - [ ] No commented-out code
  - [ ] No debug print statements
  - [ ] All functions have proper error handling
  - [ ] Logging implemented appropriately
- [ ] **Documentation Final Check**:
  - [ ] User guide complete with examples
  - [ ] API documentation with all endpoints
  - [ ] Troubleshooting guide with common issues
  - [ ] Configuration guide with all options
- [ ] **Test Results Final Check**:
  - [ ] All test outputs pasted
  - [ ] Coverage report included
  - [ ] Performance benchmarks documented
  - [ ] Security scan results included

### Handoff Preparation
- [ ] **Create handoff package**:
  - [ ] Summary of changes made
  - [ ] List of new features/capabilities
  - [ ] Known limitations or issues
  - [ ] Suggested future improvements
- [ ] **Update all document statuses**:
  - [ ] PRD status → "COMPLETE"
  - [ ] Tech Spec status → "IMPLEMENTED"
  - [ ] Test Results status → "COMPLETE"
  - [ ] Documentation status → "PUBLISHED"

## ⚠️ CRITICAL Requirements

### Never Skip These
1. **ALWAYS paste actual test output** - No summaries or "tests passed"
2. **ALWAYS check context7 MCP** when unsure about standards
3. **ALWAYS document WHY** for design decisions
4. **ALWAYS test error scenarios** - Not just happy paths
5. **ALWAYS update documentation** before marking complete

### Red Flags to Avoid
- ❌ "All tests passing" without pasted output
- ❌ "Implemented as specified" without details
- ❌ "Documentation updated" without specifics
- ❌ "Following best practices" without evidence
- ❌ Quick fixes without proper testing
- ❌ Skipping error handling "for now"
- ❌ Assuming standards without checking context7

### Evidence Requirements
For each major task, provide:
1. **Before state** - What existed before changes
2. **Changes made** - Specific files and functions modified
3. **After state** - What exists after changes
4. **Verification** - How you proved it works

## 📊 Progress Tracking

### Daily Updates Required
At the end of each work session, update progress log with:
```markdown
## Progress Update - [DATE]

### Completed Today:
- [ ] Task 1: [Specific accomplishment with evidence]
- [ ] Task 2: [Specific accomplishment with evidence]

### Blockers:
- [Any issues encountered]

### Next Steps:
- [ ] Task 1: [What will be done next]
- [ ] Task 2: [What will be done next]

### Evidence:
- Test output: [paste relevant output]
- Coverage: XX%
- Performance: [metrics]
```

## 🎯 Success Criteria

Before marking ANY task complete, verify:
1. **Functional** - Feature works as specified
2. **Tested** - Tests exist and pass (with output proof)
3. **Documented** - All docs updated
4. **Performant** - Meets performance requirements
5. **Secure** - No security vulnerabilities
6. **Maintainable** - Code is clean and well-structured

---

**Remember**: The goal is not speed, but robust, well-documented, thoroughly tested solutions. Take the time to do it right. Your work will be verified against this checklist.