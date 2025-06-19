# AI Agent Work Review Template

**Review Date**: YYYY-MM-DD  
**Reviewer Name**: [Your Name]  
**Feature/Task**: [FEATURE_NAME]  
**AI Agent/System**: [Which AI system completed the work]  
**Review Duration**: [Time spent reviewing]  

## 📊 Review Summary

### Overall Assessment
- [ ] **APPROVED** - Work meets all requirements
- [ ] **APPROVED WITH CONDITIONS** - Minor fixes needed
- [ ] **NEEDS REVISION** - Significant issues found
- [ ] **REJECTED** - Major rework required

### Quality Score
| Category | Score (1-10) | Weight | Weighted Score |
|----------|--------------|---------|----------------|
| Completeness | 0 | 25% | 0.0 |
| Code Quality | 0 | 25% | 0.0 |
| Testing | 0 | 25% | 0.0 |
| Documentation | 0 | 25% | 0.0 |
| **TOTAL** | - | 100% | **0.0** |

### Quick Stats
- **Checklist Items Completed**: ___/___
- **Test Coverage Achieved**: ___%
- **Bugs Found During Review**: ___
- **Documentation Pages Created**: ___

## 📁 Document Verification

### Required Documents Check
| Document | Exists | Status Correct | Properly Linked | Content Quality | Issues |
|----------|---------|----------------|-----------------|-----------------|---------|
| PRD | ☐ Yes ☐ No | ☐ Yes ☐ No | ☐ Yes ☐ No | ☐ Good ☐ Fair ☐ Poor | |
| Tech Spec | ☐ Yes ☐ No | ☐ Yes ☐ No | ☐ Yes ☐ No | ☐ Good ☐ Fair ☐ Poor | |
| Test Results | ☐ Yes ☐ No | ☐ Yes ☐ No | ☐ Yes ☐ No | ☐ Good ☐ Fair ☐ Poor | |
| Documentation | ☐ Yes ☐ No | ☐ Yes ☐ No | ☐ Yes ☐ No | ☐ Good ☐ Fair ☐ Poor | |

### Document Content Review

#### PRD Review
- [ ] Problem statement is clear and accurate
- [ ] Success criteria are measurable
- [ ] Dependencies properly identified
- [ ] Risk assessment is comprehensive
- [ ] Service impact analysis completed
- [ ] Timeline is realistic

**PRD Issues Found**:
```
[List specific issues]
```

#### Technical Specification Review
- [ ] Architecture design is sound
- [ ] All integration points identified
- [ ] Security considerations addressed
- [ ] Performance requirements defined
- [ ] External systems impact documented
- [ ] Context7 MCP consultation evidence present

**Tech Spec Issues Found**:
```
[List specific issues]
```

## 🧪 Test Verification

### Test Evidence Review
- [ ] **Actual test output pasted** (not summaries)
- [ ] **Coverage report included** and meets >80% requirement
- [ ] **All test types executed**:
  - [ ] Unit tests
  - [ ] Integration tests
  - [ ] Performance tests
  - [ ] Security tests
- [ ] **Edge cases tested**
- [ ] **Error scenarios tested**

### Test Output Verification
```
☐ VERIFIED: Test outputs appear genuine and complete
☐ SUSPICIOUS: Test outputs may be fabricated or incomplete
☐ MISSING: Required test outputs not provided

Notes: [Specific observations about test outputs]
```

### Test Quality Assessment
| Test Type | Coverage | Quality | Real Output? | Comments |
|-----------|----------|---------|--------------|----------|
| Unit Tests | __% | ☐High ☐Med ☐Low | ☐Yes ☐No | |
| Integration | __% | ☐High ☐Med ☐Low | ☐Yes ☐No | |
| E2E Tests | __% | ☐High ☐Med ☐Low | ☐Yes ☐No | |
| Performance | N/A | ☐High ☐Med ☐Low | ☐Yes ☐No | |

## 💻 Code Review

### Code Quality Checklist
- [ ] **Follows project coding standards** (verified against context7 MCP)
- [ ] **All functions have docstrings**
- [ ] **Complex logic is well-commented**
- [ ] **No TODO comments remaining**
- [ ] **No commented-out code**
- [ ] **Error handling implemented**
- [ ] **Logging added appropriately**
- [ ] **No obvious security vulnerabilities**

### Code Review Findings
| File | Issue Type | Severity | Description |
|------|------------|----------|-------------|
| [filename] | [Style/Logic/Security] | HIGH/MED/LOW | [Description] |

### Code Patterns Review
- [ ] **Consistent with existing codebase**
- [ ] **No anti-patterns detected**
- [ ] **Proper separation of concerns**
- [ ] **DRY principle followed**
- [ ] **SOLID principles applied**

**Pattern Violations Found**:
```
[List specific violations]
```

## 📚 Documentation Review

### Documentation Completeness
- [ ] **User documentation**
  - [ ] Getting started guide
  - [ ] Feature documentation
  - [ ] Configuration guide
  - [ ] Examples provided
- [ ] **API documentation**
  - [ ] All endpoints documented
  - [ ] Request/response examples
  - [ ] Error codes explained
  - [ ] Authentication documented
- [ ] **Developer documentation**
  - [ ] Setup instructions work
  - [ ] Architecture explained
  - [ ] Contributing guidelines
- [ ] **Operations documentation**
  - [ ] Deployment guide
  - [ ] Monitoring setup
  - [ ] Troubleshooting guide
  - [ ] Runbook complete

### Documentation Quality
| Section | Accuracy | Clarity | Completeness | Examples | Score |
|---------|----------|---------|--------------|----------|--------|
| User Guide | ☐Y ☐N | ☐Good ☐Fair ☐Poor | ☐Y ☐N | ☐Y ☐N | _/10 |
| API Docs | ☐Y ☐N | ☐Good ☐Fair ☐Poor | ☐Y ☐N | ☐Y ☐N | _/10 |
| Dev Docs | ☐Y ☐N | ☐Good ☐Fair ☐Poor | ☐Y ☐N | ☐Y ☐N | _/10 |
| Ops Docs | ☐Y ☐N | ☐Good ☐Fair ☐Poor | ☐Y ☐N | ☐Y ☐N | _/10 |

## 🚨 Red Flag Detection

### AI Agent Behavior Patterns
- [ ] **"Completion Theater"** - Claims without evidence
- [ ] **Skipped Tests** - Tests mentioned but not run
- [ ] **Generic Documentation** - Copy-paste or boilerplate
- [ ] **No Error Handling** - Only happy path implemented
- [ ] **Fake Outputs** - Test results that look fabricated
- [ ] **Pattern Ignorance** - Didn't follow existing patterns
- [ ] **Quick Fixes** - Hacky solutions instead of proper ones

### Evidence of Shortcuts
```
[Document any suspicious patterns or shortcuts taken]
```

## ✅ Verification Results

### Functional Verification
- [ ] **Feature works as specified**
  - [ ] All acceptance criteria met
  - [ ] Manual testing performed
  - [ ] No regression issues
- [ ] **Performance acceptable**
  - [ ] Meets latency requirements
  - [ ] Handles expected load
  - [ ] Resource usage reasonable

### Integration Verification
- [ ] **No breaking changes to other services**
- [ ] **API contracts maintained**
- [ ] **Database migrations safe**
- [ ] **Backward compatibility preserved**

### Security Verification
- [ ] **Security scan results clean**
- [ ] **No exposed secrets**
- [ ] **Input validation present**
- [ ] **Authentication/authorization correct**

## 🔧 Required Fixes

### Critical Issues (Must Fix)
1. **Issue**: [Description]
   - **Location**: [Where found]
   - **Impact**: [What it affects]
   - **Required Fix**: [What needs to be done]

### Major Issues (Should Fix)
1. **Issue**: [Description]
   - **Location**: [Where found]
   - **Impact**: [What it affects]
   - **Suggested Fix**: [What should be done]

### Minor Issues (Nice to Fix)
1. **Issue**: [Description]
   - **Location**: [Where found]
   - **Improvement**: [What could be better]

## 📈 Performance Metrics

### AI Agent Performance
| Metric | Expected | Actual | Variance |
|--------|----------|---------|----------|
| Completion Time | X days | Y days | +/-Z days |
| Rework Required | <10% | X% | +/-Y% |
| Defect Rate | <5% | X% | +/-Y% |
| Doc Completeness | 100% | X% | -Y% |

### Quality Metrics
| Metric | Target | Achieved | Pass/Fail |
|--------|---------|----------|-----------|
| Code Coverage | >80% | X% | ☐Pass ☐Fail |
| Documentation | Complete | X% | ☐Pass ☐Fail |
| Tests Passing | 100% | X% | ☐Pass ☐Fail |
| Performance | Met | ☐Yes ☐No | ☐Pass ☐Fail |

## 💬 Detailed Review Comments

### What Was Done Well
```
[Specific examples of good work]
- 
- 
- 
```

### What Needs Improvement
```
[Specific areas that need work]
- 
- 
- 
```

### Lessons Learned
```
[Insights for improving AI agent instructions or process]
- 
- 
- 
```

## 🎯 Recommendations

### For This Feature
- [ ] **APPROVE** - Ready for production
- [ ] **REVISE** - Fix critical issues and resubmit
- [ ] **REWORK** - Significant changes needed
- [ ] **ESCALATE** - Need human developer intervention

### For Future AI Agent Work
1. **Process Improvements**:
   - [Suggestion 1]
   - [Suggestion 2]

2. **Instruction Clarifications**:
   - [What needs to be clearer]
   - [What was misunderstood]

3. **Additional Checks Needed**:
   - [New verification steps]
   - [Additional requirements]

## 📎 Review Artifacts

### Screenshots/Evidence
- [ ] Manually tested features (attach screenshots)
- [ ] Performance test results verified
- [ ] Integration test results verified
- [ ] Security scan results verified

### Review Tools Used
- [ ] Code review tool: [Name]
- [ ] Test runner: [Name]
- [ ] Performance profiler: [Name]
- [ ] Security scanner: [Name]

## ✍️ Sign-off

### Reviewer Certification
I certify that I have:
- [ ] Reviewed all submitted documents
- [ ] Verified test outputs are genuine
- [ ] Manually tested key functionality
- [ ] Checked code against standards
- [ ] Validated documentation accuracy

**Reviewer Signature**: _________________________  
**Date**: YYYY-MM-DD  
**Time Spent on Review**: _____ hours

### Escalation Required?
- [ ] No escalation needed
- [ ] Escalate to: [Name/Role]
- [ ] Reason: [Why escalation needed]

---

## 📊 Review Analytics Dashboard

### Review Efficiency
- Documents Reviewed: ___
- Issues Found: ___
- False Positives: ___
- Time per Issue: ___ minutes

### AI Agent Scorecard
| Criterion | This Review | Historical Avg | Trend |
|-----------|------------|----------------|--------|
| Completeness | X% | Y% | ↑↓→ |
| Quality | X% | Y% | ↑↓→ |
| Accuracy | X% | Y% | ↑↓→ |
| Following Instructions | X% | Y% | ↑↓→ |

### Action Items for AI Training
1. [ ] Update prompts for: [Area needing improvement]
2. [ ] Add examples for: [Confusing areas]
3. [ ] Clarify requirements for: [Misunderstood parts]
4. [ ] Add validation for: [Common errors]

---

**Review Template Version**: 1.0  
**Next Review**: [When to review this agent's work again]  
**CC**: [Stakeholders to notify]