# Story Audit Checklist - Sprint Framework Compliance

## Purpose
Use this checklist to audit existing stories marked as "Complete" to determine if they actually meet proper sprint framework standards. Stories that fail this audit should have their status downgraded until proper review gates are completed.

## Audit Instructions

1. **Review each story** listed in the audit scope below
2. **Score each section** using the criteria provided
3. **Calculate overall compliance** percentage
4. **Recommend status changes** based on compliance score

### **Compliance Scoring:**
- **90-100%:** ✅ COMPLIANT - Story properly complete
- **70-89%:** ⚠️ MINOR GAPS - Address issues but may remain "Complete" 
- **50-69%:** 🔄 MAJOR GAPS - Downgrade to "Implementation Complete"
- **<50%:** ❌ NON-COMPLIANT - Downgrade to "In Progress" or "Draft"

## Story Audit Form

### **Story Information**
- **Story ID:** [e.g., 2.2]
- **Title:** [Story Title]
- **Current Status:** [Current claimed status]
- **Audit Date:** [Date]
- **Auditor:** [Name]

### **Section 1: Story Framework (25 points)**

#### **Story Points Estimation (5 points)**
- [ ] **5 pts:** Story points estimated and documented
- [ ] **3 pts:** Rough estimation provided but not formalized
- [ ] **1 pt:** Estimation attempted but incomplete
- [ ] **0 pts:** No story points estimation

**Score:** ___/5

#### **Dependencies Documentation (10 points)**
- [ ] **10 pts:** Complete dependencies section with required/external deps
- [ ] **7 pts:** Some dependencies identified but incomplete
- [ ] **3 pts:** Minimal dependency documentation
- [ ] **0 pts:** No dependencies section

**Score:** ___/10

#### **Acceptance Criteria Quality (10 points)**
- [ ] **10 pts:** Specific, measurable, testable acceptance criteria
- [ ] **7 pts:** Adequate AC but some vagueness
- [ ] **3 pts:** Basic AC present but needs improvement
- [ ] **0 pts:** No clear acceptance criteria

**Score:** ___/10

**Section 1 Total:** ___/25

### **Section 2: Risk Management & Planning (20 points)**

#### **Risk & Mitigation Section (15 points)**
- [ ] **15 pts:** Comprehensive risks identified with mitigation strategies
- [ ] **10 pts:** Some risks identified with basic mitigation
- [ ] **5 pts:** Minimal risk documentation
- [ ] **0 pts:** No risk section

**Score:** ___/15

#### **Stakeholder Communication Plan (5 points)**
- [ ] **5 pts:** Clear stakeholder roles and communication plan
- [ ] **3 pts:** Basic stakeholder identification
- [ ] **1 pt:** Minimal stakeholder documentation
- [ ] **0 pts:** No stakeholder communication plan

**Score:** ___/5

**Section 2 Total:** ___/20

### **Section 3: Definition of Done & Quality (30 points)**

#### **Definition of Done Section (20 points)**
- [ ] **20 pts:** Comprehensive DoD with 8+ specific criteria
- [ ] **15 pts:** Good DoD with 5-7 criteria
- [ ] **10 pts:** Basic DoD with 3-4 criteria
- [ ] **5 pts:** Minimal DoD documentation
- [ ] **0 pts:** No Definition of Done section

**Score:** ___/20

#### **Quality Gates Evidence (10 points)**
- [ ] **10 pts:** Evidence of code review, testing, peer review
- [ ] **7 pts:** Some quality evidence but incomplete
- [ ] **3 pts:** Minimal quality documentation
- [ ] **0 pts:** No quality evidence

**Score:** ___/10

**Section 3 Total:** ___/30

### **Section 4: Acceptance & Documentation (25 points)**

#### **Product Owner Acceptance (10 points)**
- [ ] **10 pts:** Documented Product Owner formal sign-off
- [ ] **7 pts:** Clear acceptance mentioned but not formal
- [ ] **3 pts:** Implied acceptance but not documented
- [ ] **0 pts:** No evidence of Product Owner acceptance

**Score:** ___/10

#### **Implementation Evidence (10 points)**
- [ ] **10 pts:** Clear evidence of implementation (code, tests, demos)
- [ ] **7 pts:** Good implementation evidence
- [ ] **3 pts:** Some implementation evidence
- [ ] **0 pts:** No implementation evidence

**Score:** ___/10

#### **Documentation Quality (5 points)**
- [ ] **5 pts:** Comprehensive documentation updated
- [ ] **3 pts:** Adequate documentation
- [ ] **1 pt:** Minimal documentation
- [ ] **0 pts:** No documentation updates

**Score:** ___/5

**Section 4 Total:** ___/25

## **Audit Summary**

### **Total Score Calculation:**
- Section 1 (Story Framework): ___/25
- Section 2 (Risk Management): ___/20  
- Section 3 (Definition of Done): ___/30
- Section 4 (Acceptance): ___/25

**TOTAL SCORE:** ___/100

**COMPLIANCE PERCENTAGE:** ___%

### **Audit Recommendation:**
- [ ] ✅ **COMPLIANT** (90-100%) - Story properly complete
- [ ] ⚠️ **MINOR GAPS** (70-89%) - Address issues, may remain "Complete"
- [ ] 🔄 **MAJOR GAPS** (50-69%) - Downgrade to "Implementation Complete"  
- [ ] ❌ **NON-COMPLIANT** (<50%) - Downgrade to "In Progress" or "Draft"

### **Required Actions:**
1. [List specific actions needed to achieve compliance]
2. [Additional actions...]
3. [etc...]

### **Recommended New Status:** [New status recommendation]

### **Follow-up Timeline:** [When to re-audit]

---

## **Audit Scope - Stories Requiring Review**

### **High Priority Audit (Immediate):**
- [ ] **Story 2.2** - Status: "Complete" - [Audit Date: ___]
- [ ] **Story 2.3** - Status: "Completed" - [Audit Date: ___]
- [ ] **Story 2.4** - Status: "✅ FULLY COMPLETED" - [Audit Date: ___]
- [ ] **Story 2.5** - Status: "COMPLETED ✅" - [Audit Date: ___]
- [ ] **Story 2.6** - Status: "Completed" - [Audit Date: ___]

### **Medium Priority Audit (Next Week):**
- [ ] **Story 1.1** - Status: [Check status] - [Audit Date: ___]
- [ ] **Story 1.2** - Status: [Check status] - [Audit Date: ___]
- [ ] **Story 1.3** - Status: [Check status] - [Audit Date: ___]
- [ ] **Story 1.4** - Status: "Review" - [Audit Date: ___]
- [ ] **Story 2.1** - Status: "Review" - [Audit Date: ___]

### **Verified Compliant (No Audit Needed):**
- [x] **Story 2.7** - ✅ Framework complete (recently updated)
- [x] **Story 3.1** - ✅ Framework complete (recently updated)
- [x] **Story 3.2** - ✅ Framework complete (recently updated)
- [x] **Story 3.3** - ✅ Framework complete (recently updated)

## **Audit Results Summary Template**

```markdown
# Story Audit Results - [Date]

## Executive Summary
- **Stories Audited:** [Number]
- **Compliance Rate:** [%]
- **Status Changes Required:** [Number]

## Detailed Results:
| Story | Current Status | Audit Score | Compliance | Recommended Status | Priority |
|-------|---------------|-------------|------------|-------------------|----------|
| 2.2   | Complete      | __/100     | __%        | [New Status]      | High     |
| 2.3   | Completed     | __/100     | __%        | [New Status]      | High     |
| ...   | ...           | ...        | ...        | ...               | ...      |

## Immediate Actions Required:
1. [Action 1 - Owner - Due Date]
2. [Action 2 - Owner - Due Date]
3. [etc...]

## Process Improvements Identified:
1. [Improvement 1]
2. [Improvement 2]
3. [etc...]
```

---

**Document Owner:** Scrum Master (Fran)  
**Last Updated:** [Current Date]
**Next Review:** After completion of all high-priority audits 