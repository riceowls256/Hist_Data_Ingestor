# Project Kickoff Prompt

## Context
You are about to start implementing a new feature. This prompt ensures you follow our documentation standards and processes from the beginning.

## Prompt

I need you to implement [FEATURE_NAME]. Before you begin any coding, you must complete the planning phase properly.

### Phase 1: Setup and Planning

1. **Read and understand all templates**:
   - Review `.aidocs/templates/AI_AGENT_CHECKLIST.md`
   - Review `.aidocs/templates/BEGINNERS_GUIDE_WHERE_EVERYTHING_GOES.md`
   - Understand the Epic → Story → Task → Subtask hierarchy

2. **Create all required documents** in `/prds/active/`:
   - `[FEATURE_NAME]_PRD.md` - Use PRD template v2.0
   - `[FEATURE_NAME]_TECH_SPEC.md` - Use Tech Spec template v4.0
   - `[FEATURE_NAME]_TEST_RESULTS.md` - Use Test Results template v1.0
   - `[FEATURE_NAME]_DOCS.md` - Use Documentation template v1.0

3. **Check coding standards**:
   - Use context7 MCP server to understand current project patterns
   - Document findings in Tech Spec

### Requirements for [FEATURE_NAME]

**Epic**: [High-level feature group]

**User Stories**:
1. As a [user type], I want to [action], so that [benefit]
2. As a [user type], I want to [action], so that [benefit]

**Key Requirements**:
- [Requirement 1]
- [Requirement 2]
- [Requirement 3]

**Success Criteria**:
- [ ] [Measurable criterion]
- [ ] [Measurable criterion]
- [ ] [Measurable criterion]

**Constraints**:
- Must integrate with [existing system]
- Performance: [specific requirements]
- Security: [specific requirements]

### Your First Tasks

1. **Complete PRD sections**:
   - Break down the epic into stories
   - Break stories into tasks and subtasks
   - Estimate hours for each task
   - Identify dependencies
   - Complete risk assessment

2. **Complete Technical Specification**:
   - Design architecture
   - Define git workflow
   - Map all service dependencies
   - Plan database schema
   - Design API endpoints

3. **Set up development environment**:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/[FEATURE_NAME]
   ```

4. **Create initial project structure** and update all document statuses to "DRAFT"

### Important Reminders

- NO CODING until planning documents are complete and reviewed
- Every design decision must be documented with reasoning
- Check context7 MCP for existing patterns before creating new ones
- Follow TDD - write tests first
- Commit after each completed subtask

Begin by creating the four required documents and completing the PRD's epic and story breakdown.
