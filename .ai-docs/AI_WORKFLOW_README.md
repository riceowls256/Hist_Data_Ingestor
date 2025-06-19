# AI Documentation Workflow Guide

A comprehensive guide for using AI agents with structured documentation templates to build high-quality software projects.

## 🎯 Overview

This workflow ensures AI agents produce well-documented, thoroughly tested, production-ready code by following a structured process with mandatory documentation at each step.

### Key Principles
- **Documentation First** - Plan before coding
- **Test Driven Development** - Write tests before implementation
- **Evidence Based Progress** - Paste actual outputs, not summaries
- **No Shortcuts** - Quality over speed

## 📁 Directory Structure

```
.aidocs/
├── templates/           # Document templates
│   ├── PRD_TEMPLATE.md (v2.0)
│   ├── TECH_SPEC_TEMPLATE.md (v4.0)
│   ├── TEST_RESULTS_TEMPLATE.md (v1.0)
│   ├── DOCUMENTATION_TEMPLATE.md (v1.0)
│   ├── AI_AGENT_CHECKLIST.md (v1.0)
│   ├── AI_WORK_REVIEW_TEMPLATE.md (v1.0)
│   └── BEGINNERS_GUIDE_WHERE_EVERYTHING_GOES.md (v1.0)
├── prompts/            # AI orchestration prompts
│   ├── 01_PROJECT_KICKOFF.md
│   ├── 02_DAILY_STATUS_CHECK.md
│   ├── 03_COURSE_CORRECTION.md
│   ├── 04_BLOCKED_ESCALATION.md
│   ├── 05_TESTING_VALIDATION.md
│   ├── 06_HANDOFF_COMPLETION.md
│   ├── 07_QUICK_TASK.md
│   ├── 08_DEBUG_INVESTIGATION.md
│   ├── 09_PERFORMANCE_OPTIMIZATION.md
│   └── 10_REVIEW_CHECKLIST.md
└── instructions/       # Usage guides
```

## 🚀 Getting Started

### Initial Setup

1. **Install the AI documentation templates**:
   ```bash
   python setup_aidocs.py
   ```

2. **Install the prompt templates**:
   ```bash
   python setup_prompts.py
   ```

3. **Generate your first prompt**:
   ```bash
   python prompt_generator.py
   ```

## 📋 Step-by-Step Workflow

### Phase 1: Project Planning

#### Step 1: Generate Project Kickoff Prompt
```bash
python prompt_generator.py
# Select: 1 (Project Kickoff)
# Fill in: Feature name, requirements, etc.
```

#### Step 2: Send to AI Agent
Copy the generated prompt and send to your AI agent. The AI will create:
- `[FEATURE_NAME]_PRD.md` in `/prds/active/`
- `[FEATURE_NAME]_TECH_SPEC.md` in `/prds/active/`
- `[FEATURE_NAME]_TEST_RESULTS.md` in `/prds/active/`
- `[FEATURE_NAME]_DOCS.md` in `/prds/active/`

#### Step 3: Review Planning Documents
Check that the AI has:
- ✅ Created all 4 documents
- ✅ Broken down work into Epics → Stories → Tasks → Subtasks
- ✅ Identified all dependencies
- ✅ Completed risk assessment
- ✅ Defined measurable success criteria

### Phase 2: Development

#### Step 4: Daily Development Cycle

**Each day during development**:

1. **Morning: Get Status Update**
   ```bash
   python prompt_generator.py
   # Select: 2 (Daily Status Check)
   ```
   
   AI provides:
   - Current progress with evidence
   - Test coverage metrics
   - Blockers
   - Today's plan

2. **During Day: Monitor Progress**
   - Ensure AI follows TDD (tests first)
   - Check commits are atomic with good messages
   - Verify documentation updates

3. **If Blocked**: 
   ```bash
   python prompt_generator.py
   # Select: 4 (Blocked Escalation)
   ```

#### Step 5: Handle Changes
If requirements change:
```bash
python prompt_generator.py
# Select: 3 (Course Correction)
```

### Phase 3: Quality Assurance

#### Step 6: Testing Validation
Before any feature is marked complete:
```bash
python prompt_generator.py
# Select: 5 (Testing Validation)
```

AI must provide:
- Unit test output (>80% coverage)
- Integration test results
- Performance test metrics
- Security scan results

#### Step 7: Code Review
```bash
python prompt_generator.py
# Select: 10 (Review Checklist)
```

### Phase 4: Completion

#### Step 8: Final Handoff
```bash
python prompt_generator.py
# Select: 6 (Handoff Completion)
```

AI creates:
- Handoff package
- Final documentation
- Knowledge transfer notes

#### Step 9: Human Review
Use the review template to verify work:
```bash
cat .aidocs/templates/AI_WORK_REVIEW_TEMPLATE.md
```

Score the work on:
- Completeness
- Code Quality
- Testing
- Documentation

#### Step 10: Archive
Move completed documents:
```bash
mv prds/active/[FEATURE_NAME]_*.md prds/complete/
```

## 🎯 Workflow for Different Scenarios

### Quick Tasks (< 4 hours)
```bash
python prompt_generator.py
# Select: 7 (Quick Task)
```
Still requires tests and documentation, but simplified process.

### Bug Fixes
```bash
python prompt_generator.py
# Select: 8 (Debug Investigation)
```
Systematic approach to finding and fixing bugs.

### Performance Issues
```bash
python prompt_generator.py
# Select: 9 (Performance Optimization)
```
Data-driven optimization with before/after metrics.

## 📊 Quality Gates

### Gate 1: Planning → Development
- [ ] PRD complete with all sections
- [ ] Tech Spec reviewed
- [ ] Test plan created
- [ ] All questions answered

### Gate 2: Development → Testing  
- [ ] All code complete
- [ ] Unit tests passing (>80% coverage)
- [ ] Documentation updated
- [ ] No TODO comments

### Gate 3: Testing → Deployment
- [ ] All tests passing
- [ ] Performance requirements met
- [ ] Security scan clean
- [ ] Documentation finalized

## 🔍 What to Look For

### Red Flags 🚩
- "Tests are passing" without pasted output
- Generic documentation
- No error handling
- Missing edge case tests
- Skipped security considerations

### Green Flags ✅
- Actual test output pasted
- Specific error messages handled
- Performance metrics provided
- Clear documentation with examples
- Proper git history

## 💡 Tips for Success

### 1. Be Specific in Prompts
❌ "Build user authentication"
✅ "Build email/password authentication with JWT tokens, rate limiting, and password reset"

### 2. Enforce Evidence
Always require:
- Test command output
- Coverage reports
- Performance metrics
- Screenshots for UI

### 3. Review Incrementally
Don't wait until the end:
- Review PRD before development
- Check tests as they're written
- Validate documentation updates

### 4. Use the Checklist
The AI Agent Checklist is your friend:
```bash
cat .aidocs/templates/AI_AGENT_CHECKLIST.md
```

## 📈 Metrics to Track

### Per Feature
- Time: Estimated vs Actual
- Test Coverage: Target >80%
- Bugs Found: During development vs after
- Documentation: Pages created

### Per AI Agent
- Completion rate
- Rework required
- Documentation quality
- Following instructions

## 🛠️ Troubleshooting

### AI Not Following Templates?
1. Reference specific template sections
2. Ask to confirm template usage
3. Request evidence of compliance

### Poor Test Coverage?
1. Use Testing Validation prompt
2. Require specific edge cases
3. Ask for coverage report screenshot

### Documentation Lacking?
1. Reference Documentation template
2. Ask for specific examples
3. Require user journey documentation

## 🔄 Continuous Improvement

### Weekly Reviews
1. What worked well?
2. What challenges occurred?
3. How can prompts be improved?
4. Are templates sufficient?

### Update Templates
Based on learnings:
- Add missing sections
- Clarify confusing parts
- Add more examples

## 📚 Quick Reference

### Essential Commands
```bash
# Generate a prompt
python prompt_generator.py

# Check templates
ls .aidocs/templates/

# View checklist
cat .aidocs/templates/AI_AGENT_CHECKLIST.md

# Review work
cat .aidocs/templates/AI_WORK_REVIEW_TEMPLATE.md
```

### Prompt Selection Guide
- **New Feature**: Use #1 (Project Kickoff)
- **Daily Update**: Use #2 (Status Check)
- **Problems**: Use #4 (Blocked) or #8 (Debug)
- **Changes**: Use #3 (Course Correction)
- **Completion**: Use #5 (Testing) then #6 (Handoff)

### Document Status Flow
```
DRAFT → IN_REVIEW → APPROVED → IN_DEVELOPMENT → COMPLETE
```

## 🎓 Learning Resources

### For New Users
1. Start with: `BEGINNERS_GUIDE_WHERE_EVERYTHING_GOES.md`
2. Read one template fully before starting
3. Try a quick task first (#7)

### For AI Agents
Always reference:
- The checklist for process
- Templates for structure  
- Context7 MCP for code standards

## 🚦 Success Criteria

You know the workflow is working when:
- ✅ Every feature has 4 documents
- ✅ Test coverage consistently >80%
- ✅ No production bugs from completed features
- ✅ Documentation is actually helpful
- ✅ New team members can understand the code

---

Remember: **The goal is not speed, but sustainable, high-quality development.**

> "An hour of planning saves ten hours of debugging." - Every developer eventually

For questions or improvements, review the templates and prompts in `.aidocs/`