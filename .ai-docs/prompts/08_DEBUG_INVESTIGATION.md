# Debug and Investigation Prompt

## Context
Use this when you need the AI to investigate issues, debug problems, or analyze existing code.

## Prompt

I need you to investigate [ISSUE_DESCRIPTION] in [FEATURE_NAME/COMPONENT]. Approach this systematically and document your findings.

### Investigation Scope

**Issue Type**: BUG | PERFORMANCE | SECURITY | BEHAVIOR | UNKNOWN
**Severity**: CRITICAL | HIGH | MEDIUM | LOW
**First Reported**: [Date/Time]
**Affects**: [Users/Components/Features affected]

**Symptoms**:
- [Symptom 1]
- [Symptom 2]
- [Symptom 3]

### Investigation Process

1. **Reproduce the Issue**
   
   First, confirm you can reproduce the issue:
   ```bash
   # Steps to reproduce
   1. [Step 1]
   2. [Step 2]
   3. [Step 3]
   
   # Expected result: [what should happen]
   # Actual result: [what actually happens]
   ```

2. **Gather Information**
   
   Collect relevant data:
   ```bash
   # Check logs
   grep -r "ERROR" logs/ | tail -50
   
   # Check system state
   ps aux | grep [process]
   df -h
   free -m
   
   # Check recent changes
   git log --since="2 days ago" --oneline
   ```

3. **Analyze Code**
   
   Review relevant code sections:
   - Check recent commits to affected files
   - Look for error handling gaps
   - Review related tests
   - Check for race conditions
   - Verify assumptions in code

4. **Test Hypotheses**
   
   For each potential cause:
   ```markdown
   ## Hypothesis 1: [Description]
   - Why this might be the cause: [reasoning]
   - Test method: [how to verify]
   - Test result: [what happened]
   - Conclusion: CONFIRMED | RULED_OUT | PARTIAL
   ```

5. **Root Cause Analysis**
   
   Once found, document:
   - Root cause: [exact technical cause]
   - Why it wasn't caught: [testing gap]
   - Impact analysis: [what else might be affected]
   - Timeline: [when introduced]

### Debug Output Documentation

Create `DEBUG_[ISSUE_NAME]_REPORT.md` with:

```markdown
# Debug Report: [Issue Name]

## Issue Summary
- **Description**: [Brief description]
- **Root Cause**: [Technical cause]
- **Impact**: [Who/what affected]
- **Introduced**: [When/which commit]

## Investigation Steps
[Document your investigation process]

## Evidence
[Paste relevant logs, errors, test results]

## Solution
- **Fix Applied**: [What was changed]
- **Why It Works**: [Technical explanation]
- **Side Effects**: [Any impacts]

## Prevention
- **Testing Gap**: [What test would have caught this]
- **Process Improvement**: [How to prevent similar issues]

## Verification
- **Test Added**: [New test to prevent regression]
- **Manual Testing**: [Steps to verify fix]
```

### Fix Implementation

Once root cause is found:

1. Create fix branch:
   ```bash
   git checkout -b fix/[ISSUE_NAME]
   ```

2. Implement minimal fix (no refactoring)

3. Add regression test

4. Verify fix doesn't break anything else

5. Document the fix in code comments

### Questions During Investigation

If you need information:
- [ ] Can you provide more specific error messages?
- [ ] When did this last work correctly?
- [ ] Are there any recent environment changes?
- [ ] Can you provide sample data that triggers the issue?

Report your findings at each stage, don't wait until the end.
