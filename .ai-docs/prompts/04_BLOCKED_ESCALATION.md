# Blocked Task Escalation Prompt

## Context
Use this when the AI agent is blocked and cannot proceed without human intervention.

## Prompt

I'm blocked on [FEATURE_NAME] and need escalation. Here's my detailed blocker report:

### Blocker Summary

**Task Blocked**: [Task ID] - [Task Name]
**Blocked Since**: [Date/Time]
**Impact**: CRITICAL | HIGH | MEDIUM | LOW
**Type**: TECHNICAL | DEPENDENCY | CLARIFICATION | ACCESS | DECISION

### Detailed Description

**What I was trying to do**:
```markdown
1. [Step 1 I completed]
2. [Step 2 I completed]
3. [Step 3 where I got blocked]
```

**What's blocking me**:
[Detailed description of the blocker]

**What I've tried**:
1. [Attempt 1] - Result: [what happened]
2. [Attempt 2] - Result: [what happened]
3. [Attempt 3] - Result: [what happened]

### Evidence

```bash
# Paste relevant error messages, logs, or command outputs
[ERROR OUTPUT]
```

### Dependencies

**This blocks the following tasks**:
- [ ] [Task ID]: [Task Name] - [Impact description]
- [ ] [Task ID]: [Task Name] - [Impact description]

**This affects the following stories**:
- Story [ID]: Impact: [description]
- Story [ID]: Impact: [description]

### Potential Solutions

I've identified these potential solutions:

1. **Option A**: [Description]
   - Pros: [list]
   - Cons: [list]
   - Effort: [estimate]

2. **Option B**: [Description]
   - Pros: [list]
   - Cons: [list]
   - Effort: [estimate]

3. **Option C**: Request human intervention for [specific action]

### Required Decisions/Actions

- [ ] [Decision needed from stakeholder]
- [ ] [Technical clarification needed]
- [ ] [Access/permissions needed]
- [ ] [Dependency that needs to be resolved]

### Workaround Plan

While blocked, I can work on:
1. [Alternative task 1] - [estimated time]
2. [Alternative task 2] - [estimated time]
3. [Documentation updates] - [estimated time]

### Impact on Timeline

Current milestone at risk: [Milestone name] - [Original date]
Estimated delay if not resolved by [date]: [X days]
Recommended new timeline if we implement [solution]: [date]

Please provide guidance on how to proceed or take the necessary action to unblock this task.
