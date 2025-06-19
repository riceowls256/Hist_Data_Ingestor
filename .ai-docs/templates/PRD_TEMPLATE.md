# [FEATURE_NAME] Product Requirements Document

**Document Status**: DRAFT | IN_REVIEW | APPROVED | IN_DEVELOPMENT | COMPLETE  
**PRD Version**: 2.0  
**Created**: YYYY-MM-DD  
**Last Updated**: YYYY-MM-DD  
**Author**: [Name]  
**Reviewers**: [Names]  

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [Goals & Success Criteria](#goals--success-criteria)
4. [User Stories & Requirements](#user-stories--requirements)
5. [Out of Scope](#out-of-scope)
6. [Dependencies & Risks](#dependencies--risks)
7. [Timeline & Milestones](#timeline--milestones)
8. [Companion Documents](#companion-documents)
9. [Approval & Sign-off](#approval--sign-off)
10. [Change Log](#change-log)

## Executive Summary
[2-3 paragraph overview of what this feature/project is about, why it's important, and what it will achieve]

### Key Stakeholders
- **Product Owner**: [Name]
- **Technical Lead**: [Name]
- **QA Lead**: [Name]
- **Implementation Team**: [Names/Team]

## Problem Statement

### Current State
[Describe the current situation, pain points, and why change is needed]

### Desired Future State
[Describe what success looks like after implementation]

### Impact of Not Solving
[What happens if we don't address this? Quantify if possible]

## Goals & Success Criteria

### Primary Goals
1. [Specific, measurable goal]
2. [Specific, measurable goal]
3. [Specific, measurable goal]

### Success Metrics
| Metric | Current Value | Target Value | Measurement Method |
|--------|--------------|--------------|-------------------|
| [Metric 1] | X | Y | How to measure |
| [Metric 2] | X | Y | How to measure |

### Acceptance Criteria
- [ ] [Specific testable criterion]
- [ ] [Specific testable criterion]
- [ ] [Specific testable criterion]

## User Stories & Requirements

### Epic Overview
| Epic ID | Epic Name | Description | Target Release |
|---------|-----------|-------------|----------------|
| E1 | [Epic Name] | [High-level feature group] | [Version/Date] |
| E2 | [Epic Name] | [High-level feature group] | [Version/Date] |

### User Stories by Epic

#### Epic E1: [Epic Name]
| Story ID | User Story | Priority | Story Points | Status |
|----------|------------|----------|--------------|--------|
| E1-S1 | As a [user], I want to [action], so that [benefit] | HIGH | 8 | NOT_STARTED |
| E1-S2 | As a [user], I want to [action], so that [benefit] | MEDIUM | 5 | NOT_STARTED |

##### Story E1-S1: [Story Title]
**Acceptance Criteria**:
- [ ] [Specific criterion]
- [ ] [Specific criterion]
- [ ] [Specific criterion]

**Tasks**:
| Task ID | Task Name | Description | Assigned To | Estimated Hours | Status |
|---------|-----------|-------------|-------------|-----------------|--------|
| E1-S1-T1 | [Task name] | [What needs to be done] | [Person/AI] | 4 | TODO |
| E1-S1-T2 | [Task name] | [What needs to be done] | [Person/AI] | 2 | TODO |

**Subtasks for E1-S1-T1**:
- [ ] E1-S1-T1.1: [Subtask description] (1h)
- [ ] E1-S1-T1.2: [Subtask description] (1h)
- [ ] E1-S1-T1.3: [Subtask description] (2h)

##### Story E1-S2: [Story Title]
[Repeat structure above]

### Functional Requirements
| ID | Requirement | Priority | Notes |
|----|------------|----------|-------|
| FR-01 | [Requirement description] | HIGH/MED/LOW | [Additional context] |
| FR-02 | [Requirement description] | HIGH/MED/LOW | [Additional context] |

### Non-Functional Requirements
| ID | Category | Requirement | Target |
|----|----------|------------|--------|
| NFR-01 | Performance | [Requirement] | [Specific target] |
| NFR-02 | Security | [Requirement] | [Specific target] |
| NFR-03 | Reliability | [Requirement] | [Specific target] |

## Out of Scope
Explicitly list what this PRD does NOT cover:
- [Feature/functionality not included]
- [Feature/functionality not included]
- [Deferred to future phase]

## Dependencies & Risks

### Dependencies
| Dependency | Type | Owner | Status | Impact if Delayed |
|------------|------|-------|--------|------------------|
| [System/Team/Resource] | Internal/External | [Name] | On Track/At Risk/Blocked | HIGH/MED/LOW |

### Risk Assessment
| Risk | Probability | Impact | Mitigation Strategy | Owner |
|------|------------|--------|-------------------|--------|
| [Risk description] | HIGH/MED/LOW | HIGH/MED/LOW | [How to prevent/handle] | [Name] |

### Services Impact Analysis
**CRITICAL: Services that could be affected by this change:**
| Service | Impact Type | Risk Level | Testing Required | Rollback Plan |
|---------|------------|------------|-----------------|---------------|
| [Service A] | [Read/Write/API] | HIGH/MED/LOW | [Specific tests] | [How to rollback] |
| [Service B] | [Performance] | HIGH/MED/LOW | [Load tests] | [How to rollback] |

## Timeline & Milestones

### Work Breakdown Structure (WBS)
```
Project
├── Epic E1: [Epic Name]
│   ├── Story E1-S1: [Story Name]
│   │   ├── Task E1-S1-T1: [Task Name]
│   │   │   ├── Subtask E1-S1-T1.1: [Subtask]
│   │   │   ├── Subtask E1-S1-T1.2: [Subtask]
│   │   │   └── Subtask E1-S1-T1.3: [Subtask]
│   │   └── Task E1-S1-T2: [Task Name]
│   └── Story E1-S2: [Story Name]
└── Epic E2: [Epic Name]
    └── Story E2-S1: [Story Name]
```

### Task Dependencies & Gantt View
| ID | Name | Type | Duration | Dependencies | Start | End | Progress |
|----|------|------|----------|--------------|-------|-----|----------|
| E1 | [Epic 1] | Epic | 20 days | - | YYYY-MM-DD | YYYY-MM-DD | 0% |
| E1-S1 | [Story 1] | Story | 5 days | - | YYYY-MM-DD | YYYY-MM-DD | 0% |
| E1-S1-T1 | [Task 1] | Task | 4 hours | - | YYYY-MM-DD | YYYY-MM-DD | 0% |
| E1-S1-T1.1 | [Subtask 1] | Subtask | 1 hour | - | YYYY-MM-DD | YYYY-MM-DD | 0% |
| E1-S1-T2 | [Task 2] | Task | 2 hours | E1-S1-T1 | YYYY-MM-DD | YYYY-MM-DD | 0% |

### Sprint Planning
| Sprint | Dates | Planned Items | Story Points | Status |
|--------|-------|---------------|--------------|--------|
| Sprint 1 | YYYY-MM-DD to YYYY-MM-DD | E1-S1, E1-S2 | 13 | PLANNING |
| Sprint 2 | YYYY-MM-DD to YYYY-MM-DD | E1-S3, E2-S1 | 15 | NOT_STARTED |

### High-Level Timeline
| Phase | Duration | Start Date | End Date | Deliverables |
|-------|----------|------------|----------|--------------|
| Planning | X days | YYYY-MM-DD | YYYY-MM-DD | PRD, Tech Spec, Test Plan |
| Development | X days | YYYY-MM-DD | YYYY-MM-DD | Code, Unit Tests, Docs |
| Testing | X days | YYYY-MM-DD | YYYY-MM-DD | Test Results, Bug Fixes |
| Deployment | X days | YYYY-MM-DD | YYYY-MM-DD | Production Release |

### Detailed Milestones
| Milestone | Date | Success Criteria | Verification Method |
|-----------|------|-----------------|-------------------|
| M1: [Name] | YYYY-MM-DD | [What defines completion] | [How to verify] |
| M2: [Name] | YYYY-MM-DD | [What defines completion] | [How to verify] |

### Quality Gates
- [ ] **Gate 1: Planning → Development**
  - [ ] PRD approved by all stakeholders
  - [ ] Technical specification complete
  - [ ] Test plan created
  - [ ] Risk mitigation strategies defined
  
- [ ] **Gate 2: Development → Testing**
  - [ ] All code complete with documentation
  - [ ] Unit tests passing (>80% coverage)
  - [ ] Code review completed
  - [ ] Integration points verified

- [ ] **Gate 3: Testing → Deployment**
  - [ ] All test scenarios passing
  - [ ] Performance benchmarks met
  - [ ] Security review completed
  - [ ] Rollback plan tested

## Companion Documents

### Required Documents
| Document | Purpose | Status | Link |
|----------|---------|--------|------|
| Technical Specification | Detailed implementation design | NOT_STARTED/IN_PROGRESS/COMPLETE | [FEATURE_NAME_TECH_SPEC.md] |
| Test Results | Verification of all testing | NOT_STARTED/IN_PROGRESS/COMPLETE | [FEATURE_NAME_TEST_RESULTS.md] |
| Documentation | User and technical docs | NOT_STARTED/IN_PROGRESS/COMPLETE | [FEATURE_NAME_DOCS.md] |

### Document Verification Checklist
- [ ] Technical specification reviewed and approved
- [ ] Test plan covers all acceptance criteria
- [ ] Documentation plan includes all user types
- [ ] All companion documents created and linked

## Approval & Sign-off

### Review Status
| Reviewer | Role | Status | Date | Comments |
|----------|------|--------|------|----------|
| [Name] | Product Owner | PENDING/APPROVED | YYYY-MM-DD | [Comments] |
| [Name] | Technical Lead | PENDING/APPROVED | YYYY-MM-DD | [Comments] |
| [Name] | QA Lead | PENDING/APPROVED | YYYY-MM-DD | [Comments] |
| [Name] | Security | PENDING/APPROVED | YYYY-MM-DD | [Comments] |

### Implementation Sign-off
- [ ] All acceptance criteria met
- [ ] All tests passing with results documented
- [ ] Documentation complete and reviewed
- [ ] No critical issues outstanding
- [ ] Rollback plan tested and ready

## Change Log

| Date | Version | Author | Changes | Reason |
|------|---------|--------|---------|--------|
| YYYY-MM-DD | 1.0 | [Name] | Initial draft | Project kickoff |
| YYYY-MM-DD | 1.1 | [Name] | [What changed] | [Why it changed] |

---

**Next Review Date**: YYYY-MM-DD  
**Document Location**: `/prds/active/FEATURE_NAME_PRD.md`