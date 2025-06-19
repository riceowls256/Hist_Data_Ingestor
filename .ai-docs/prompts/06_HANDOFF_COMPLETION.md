# Project Handoff and Completion Prompt

## Context
Use this when the AI agent indicates all work is complete and ready for final handoff.

## Prompt

You've indicated that [FEATURE_NAME] is complete. Let's perform a comprehensive handoff review to ensure everything is properly finished and documented.

### 1. Completion Checklist

Verify EVERY item is complete:

#### Code Completion
- [ ] All epic stories are COMPLETE
- [ ] All tasks and subtasks are COMPLETE
- [ ] No WIP (Work In Progress) commits
- [ ] No commented-out code remains
- [ ] No debug statements remain
- [ ] All TODOs have been addressed

#### Testing Completion
- [ ] Unit test coverage > 80%
- [ ] All integration tests passing
- [ ] All E2E tests passing
- [ ] Performance requirements met
- [ ] Security scan clean
- [ ] Test results fully documented

#### Documentation Completion
- [ ] PRD status = COMPLETE
- [ ] Tech Spec status = IMPLEMENTED
- [ ] Test Results status = COMPLETE
- [ ] User Documentation status = PUBLISHED
- [ ] API documentation complete
- [ ] Runbook/operations guide complete

### 2. Deliverables Package

Create a handoff package with:

```markdown
# [FEATURE_NAME] Handoff Package

## What Was Built
- [Summary of implemented features]
- [Key architectural decisions]
- [Technologies used]

## How to Use It
- [Quick start guide]
- [API endpoints summary]
- [Configuration required]

## How to Test It
- [Test commands]
- [Test data location]
- [Expected results]

## How to Deploy It
- [Deployment steps]
- [Environment requirements]
- [Rollback procedure]

## How to Monitor It
- [Key metrics to watch]
- [Alert thresholds]
- [Log locations]

## Known Issues/Limitations
- [Issue 1]: [Description] - [Workaround]
- [Issue 2]: [Description] - [Workaround]

## Future Improvements
- [Improvement 1]: [Description] - [Effort estimate]
- [Improvement 2]: [Description] - [Effort estimate]
```

### 3. Final Code Review

Run final checks:

```bash
# Final test run
pytest tests/ -v --cov=. --cov-report=html

# Final lint check
flake8 src/ --count --statistics

# Final security check
bandit -r src/ -ll

# Check for secrets
git secrets --scan

# Generate dependency list
pip freeze > requirements-final.txt
```

### 4. Git Cleanup

Clean up your feature branch:

```bash
# Squash commits if needed
git rebase -i main

# Ensure branch is up to date
git checkout main
git pull origin main
git checkout feature/[FEATURE_NAME]
git rebase main

# Show final changes
git diff main --stat
git log main..HEAD --oneline
```

### 5. Pull Request Preparation

Create PR with:
- Descriptive title: "feat: [FEATURE_NAME] - [Brief description]"
- Link to all 4 documents
- Summary of changes
- Testing performed
- Screenshots/demos
- Breaking changes (if any)
- Migration guide (if needed)

### 6. Knowledge Transfer

Document any special knowledge:

```markdown
## Lessons Learned
- [What went well]
- [What was challenging]
- [What would you do differently]

## Gotchas/Tips
- [Tricky part 1]: [How to handle]
- [Tricky part 2]: [How to handle]

## Dependencies to Watch
- [External service]: [What to monitor]
- [Library]: [Version constraints]
```

### 7. Final Status Report

Provide metrics:

```markdown
## Project Metrics
- Total Development Time: [actual] vs [estimated]
- Stories Completed: X/Y
- Test Coverage Achieved: X%
- Bugs Found/Fixed: X/Y
- Performance vs Requirements: [metrics]

## Velocity Data
- Story Points Completed: X
- Average Task Completion Time: [actual] vs [estimated]
- Blockers Encountered: X
```

### 8. Archive and Close

Final steps:
1. Move all documents from `/prds/active/` to `/prds/complete/`
2. Update document status to final states
3. Create git tag for the feature
4. Close any related issues/tickets

Confirm: Are all handoff requirements complete and ready for human review?
