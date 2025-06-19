# Quick Task Implementation Prompt

## Context
Use this for smaller, well-defined tasks that don't require full epic/story breakdown but still need proper documentation.

## Prompt

I need you to implement a quick task: [TASK_DESCRIPTION]. While this is smaller in scope, you must still follow our documentation and quality standards.

### Quick Task Requirements

**Task Type**: BUG_FIX | SMALL_FEATURE | REFACTOR | DOCUMENTATION | CONFIGURATION
**Estimated Time**: [X hours]
**Priority**: HIGH | MEDIUM | LOW

**Description**:
[Detailed description of what needs to be done]

**Acceptance Criteria**:
- [ ] [Specific criterion 1]
- [ ] [Specific criterion 2]
- [ ] [Specific criterion 3]

### Simplified Process

1. **Create Lightweight Documentation**:
   Create a simplified PRD named `QUICK_[TASK_NAME]_PRD.md` with:
   - Task description
   - Acceptance criteria  
   - Simple task breakdown (no epics/stories needed)
   - Test plan

2. **Technical Notes**:
   Create `QUICK_[TASK_NAME]_TECH_NOTES.md` with:
   - Implementation approach
   - Files affected
   - Risk assessment
   - Test strategy

3. **Implementation**:
   ```bash
   # Create feature branch
   git checkout -b quick/[TASK_NAME]
   ```

4. **Testing Requirements** (still mandatory):
   - Write tests for any new code
   - Run existing tests to ensure no regression
   - Document test results

5. **Code Quality** (no shortcuts):
   - Follow coding standards
   - Add proper error handling
   - Include appropriate logging
   - Update relevant documentation

### Quick Task Checklist

- [ ] Task clearly understood
- [ ] Branch created
- [ ] Implementation complete
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] Code reviewed (self-review minimum)
- [ ] No TODOs or debug code
- [ ] Commit message follows convention

### Output Required

Even for quick tasks, provide:
1. Summary of changes made
2. Test results (paste actual output)
3. List of affected files
4. Any risks or concerns
5. Verification steps

Remember: "Quick" refers to scope, not quality. Maintain the same code standards as larger features.
