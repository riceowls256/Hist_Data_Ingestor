# Code Review and Quality Check Prompt

## Context
Use this for conducting thorough code reviews or quality checks before merging.

## Prompt

Please conduct a comprehensive review of [FEATURE_NAME/PR] to ensure it meets all our quality standards.

### Review Scope

**Review Type**: FULL_FEATURE | PULL_REQUEST | SECURITY | PERFORMANCE | ARCHITECTURE
**Branch**: feature/[BRANCH_NAME]
**Files Changed**: [count]
**Lines Changed**: +[additions] -[deletions]

### Code Review Checklist

#### 1. Functionality
- [ ] Code does what it's supposed to do
- [ ] All acceptance criteria met
- [ ] No obvious bugs
- [ ] Edge cases handled
- [ ] Error scenarios handled

#### 2. Code Quality
- [ ] Follows project coding standards
- [ ] Consistent naming conventions
- [ ] No code duplication (DRY)
- [ ] Functions are single-purpose
- [ ] Appropriate abstraction levels

#### 3. Testing
- [ ] Adequate test coverage (>80%)
- [ ] Tests are meaningful, not just coverage
- [ ] Edge cases tested
- [ ] Error conditions tested
- [ ] Integration tests present

#### 4. Documentation
- [ ] All functions have docstrings
- [ ] Complex logic is commented
- [ ] README updated if needed
- [ ] API documentation complete
- [ ] No outdated comments

#### 5. Performance
- [ ] No obvious performance issues
- [ ] Efficient algorithms used
- [ ] Database queries optimized
- [ ] No memory leaks
- [ ] Caching used appropriately

#### 6. Security
- [ ] Input validation present
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] Secrets not hardcoded
- [ ] Proper authentication/authorization

#### 7. Architecture
- [ ] Follows project architecture
- [ ] Proper separation of concerns
- [ ] Dependencies injected properly
- [ ] No circular dependencies
- [ ] Interfaces used appropriately

### Automated Checks

Run these tools and paste results:

```bash
# Code formatting
black --check src/
isort --check-only src/

# Linting
flake8 src/ --count --statistics
pylint src/

# Type checking
mypy src/

# Security
bandit -r src/
safety check

# Complexity
radon cc src/ -a -nb

# Test coverage
pytest --cov=src --cov-report=term-missing
```

### Review Output Format

For each issue found:

```markdown
## Issue: [Title]
- **Severity**: CRITICAL | HIGH | MEDIUM | LOW
- **Type**: BUG | SECURITY | PERFORMANCE | STYLE | DESIGN
- **File**: [path/to/file.py:line]
- **Description**: [What's wrong]
- **Suggestion**: [How to fix]
- **Example**:
  ```python
  # Current
  [current code]
  
  # Suggested
  [improved code]
  ```
```

### Architecture Review

Review high-level design:

```markdown
## Architecture Assessment

### Strengths
- [What's well designed]
- [Good patterns used]

### Concerns
- [Potential issues]
- [Technical debt created]

### Suggestions
- [Improvement recommendations]
- [Refactoring opportunities]
```

### Pull Request Feedback

Provide summary:

```markdown
## PR Review Summary

### Overall Assessment: APPROVE | REQUEST_CHANGES | COMMENT

### Strengths
- [What was done well]

### Required Changes
- [ ] [Must fix before merge]
- [ ] [Must fix before merge]

### Suggested Improvements
- [ ] [Nice to have]
- [ ] [Can be future PR]

### Questions
- [ ] [Clarification needed]
```

### Final Checklist

Before approving:
- [ ] All tests pass
- [ ] No decrease in code coverage
- [ ] Documentation complete
- [ ] No security vulnerabilities
- [ ] Performance acceptable
- [ ] Follows architecture patterns
- [ ] No technical debt without justification

Provide clear, actionable feedback that helps improve the code.
