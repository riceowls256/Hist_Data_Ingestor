# Daily Status Check Prompt

## Context
Use this prompt to get comprehensive status updates from the AI agent during active development.

## Prompt

I need a detailed status update on the [FEATURE_NAME] implementation. Please provide the following:

### 1. Current Progress Overview

Review your task list and provide status using this format:

```markdown
## Epic E1: [Epic Name] - Overall Progress: X%

### Story E1-S1: [Story Name] - Progress: X%
| Task ID | Task Name | Status | Progress | Blockers |
|---------|-----------|---------|----------|----------|
| E1-S1-T1 | [Task] | IN_PROGRESS | 75% | None |
| E1-S1-T2 | [Task] | BLOCKED | 0% | [Describe blocker] |
| E1-S1-T3 | [Task] | COMPLETE | 100% | None |

#### Completed Subtasks Today:
- [x] E1-S1-T1.1: [Subtask] - Evidence: [paste output/commit hash]
- [x] E1-S1-T1.2: [Subtask] - Evidence: [paste output/commit hash]

#### In Progress:
- [ ] E1-S1-T1.3: [Subtask] - 50% complete, expected completion: [time]
```

### 2. Code Quality Metrics

Run and paste the following outputs:

```bash
# Test coverage
pytest --cov=. --cov-report=term-missing

# Linting
flake8 src/

# Type checking (if applicable)
mypy src/

# Security scan
bandit -r src/
```

### 3. Git Activity

Show me your recent commits:
```bash
git log --oneline -10
git status
git diff --stat origin/main...HEAD
```

### 4. Document Updates

- [ ] PRD: Last updated [when], current status: [status]
- [ ] Tech Spec: Last updated [when], current status: [status]
- [ ] Test Results: Last updated [when], test coverage: [X%]
- [ ] Documentation: Last updated [when], sections complete: [X/Y]

### 5. Blockers and Risks

| Type | Description | Impact | Proposed Solution | Need Help? |
|------|-------------|---------|------------------|------------|
| [Blocker/Risk] | [Description] | HIGH/MED/LOW | [Solution] | YES/NO |

### 6. Next 24 Hours Plan

List the specific subtasks you plan to complete:
- [ ] [Subtask ID]: [Description] (Xh)
- [ ] [Subtask ID]: [Description] (Xh)
- [ ] [Subtask ID]: [Description] (Xh)

### 7. Questions/Clarifications Needed

- [ ] [Question about requirement/implementation]
- [ ] [Question about integration point]

### 8. Demo Ready?

If you have any working features, provide:
- Screenshot/recording of working feature
- Sample API calls with responses
- Instructions to test locally

Update all relevant documents with this status information and commit your progress with appropriate conventional commit messages.
