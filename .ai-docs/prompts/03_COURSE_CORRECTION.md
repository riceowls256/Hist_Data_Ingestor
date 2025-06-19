# Course Correction Prompt

## Context
Use this when requirements change, technical approach needs adjustment, or significant issues are discovered mid-implementation.

## Prompt

We need to make a course correction on [FEATURE_NAME]. [Describe the change needed and why].

### Change Details

**What's Changing**:
- [Specific change 1]
- [Specific change 2]
- [Specific change 3]

**Why It's Changing**:
- [Business reason]
- [Technical reason]
- [User feedback]

**Impact Level**: MAJOR | MINOR | CRITICAL

### Required Actions

1. **Stop Current Work**
   - Commit any work in progress with message: `WIP: pausing for course correction`
   - Document the current state in your test results file

2. **Impact Analysis**
   
   Create a table analyzing the impact:
   ```markdown
   | Component | Current State | Required Changes | Effort | Risk |
   |-----------|--------------|------------------|--------|------|
   | [Component] | [State] | [Changes needed] | Xh | HIGH/MED/LOW |
   ```

3. **Update Planning Documents**
   
   In the PRD:
   - Add a new section: "## Course Correction - [Date]"
   - Update affected epics/stories/tasks
   - Revise estimates and dependencies
   - Add to change log with detailed reasoning

   In the Tech Spec:
   - Update architecture if needed
   - Revise API contracts if affected
   - Update risk assessment
   - Document why original approach didn't work

4. **Revise Task Breakdown**
   
   For each affected story:
   - Mark obsolete tasks as "CANCELLED" with reason
   - Add new tasks with prefix "CC-" (Course Correction)
   - Re-estimate all affected tasks
   - Update dependencies

5. **Code Changes**
   
   If code needs to be reverted or refactored:
   ```bash
   # Create a branch for the course correction
   git checkout -b feature/[FEATURE_NAME]-course-correction
   
   # If reverting specific commits
   git revert [commit-hash]
   
   # If major refactor needed
   git mv [old-structure] [new-structure]
   ```

6. **Communication Back**
   
   Provide a summary:
   - What was done before the change
   - What needs to be redone
   - What can be salvaged
   - New timeline estimate
   - Any additional resources needed

### Validation Questions

Before proceeding with changes:
- [ ] Have all stakeholders approved this change?
- [ ] Is the new approach validated against existing constraints?
- [ ] Have we considered the impact on dependent features?
- [ ] Do we need to update any external documentation?
- [ ] Are there any contractual or API compatibility issues?

### Recovery Plan

If this course correction fails:
- Rollback strategy: [describe]
- Point of no return: [when we commit to the new approach]
- Success criteria for new approach: [measurable criteria]

Document all decisions and reasoning in the change log. Update your progress tracking to reflect the new plan.
