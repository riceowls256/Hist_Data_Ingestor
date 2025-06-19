# 🚀 AI Workflow Quick-Start Cheatsheet

## 🎯 Essential Commands
```bash
python prompt_generator.py    # Generate any prompt
ls .aidocs/templates/        # View all templates  
ls .aidocs/prompts/         # View all prompts
```

## 📋 Prompt Quick Reference

| Need | Use Prompt # | When to Use |
|------|--------------|-------------|
| Start new feature | **1** | Beginning any new work |
| Get progress update | **2** | Daily status checks |
| Change requirements | **3** | Mid-project changes |
| AI is stuck | **4** | Blocked/need help |
| Validate testing | **5** | Before marking complete |
| Final handoff | **6** | Feature complete |
| Small task (<4hr) | **7** | Quick fixes/changes |
| Debug issue | **8** | Investigating bugs |
| Improve performance | **9** | Optimization needed |
| Review code | **10** | Quality check |

## 🔄 The Basic Workflow

### 1️⃣ START (New Feature)
```bash
python prompt_generator.py  # Choose 1
# AI creates 4 documents in /prds/active/
```

### 2️⃣ DAILY (During Dev)
```bash
python prompt_generator.py  # Choose 2
# Get status with evidence
```

### 3️⃣ FINISH (Complete Feature)
```bash
python prompt_generator.py  # Choose 5 (Testing)
python prompt_generator.py  # Choose 6 (Handoff)
# Move docs to /prds/complete/
```

## 📁 The 4 Required Documents

Every feature MUST have:
1. **PRD** - WHAT we're building & WHY
2. **Tech Spec** - HOW we'll build it
3. **Test Results** - PROOF it works
4. **Documentation** - HELP for users

## ✅ Quality Gates

**Planning → Dev**: PRD approved, Tech Spec complete
**Dev → Testing**: Code done, unit tests >80%
**Testing → Done**: All tests pass, docs complete

## 🚩 Red Flags to Watch For

- ❌ "Tests passing" with no output
- ❌ Generic documentation
- ❌ No error handling
- ❌ Missing test coverage number
- ❌ TODO comments still in code

## 💡 Pro Tips

1. **Always require evidence** - Make AI paste actual outputs
2. **Check coverage** - Must be >80%
3. **Use context7 MCP** - For code standards
4. **Review incrementally** - Don't wait until end
5. **No shortcuts** - Quality > Speed

## 🔍 Quick Checks

### Is AI Following Process?
```bash
# Check if all 4 docs exist
ls prds/active/*FEATURE_NAME*

# View the checklist
cat .aidocs/templates/AI_AGENT_CHECKLIST.md
```

### Review Work Quality
```bash
# Use review template
cat .aidocs/templates/AI_WORK_REVIEW_TEMPLATE.md
```

## 📊 Document Status Flow
```
DRAFT → IN_REVIEW → APPROVED → IN_DEVELOPMENT → COMPLETE
         ↓                          ↓
    (Planning Phase)         (Implementation)
```

## 🆘 When Stuck

| Problem | Solution |
|---------|----------|
| AI not using templates | Reference specific template in prompt |
| Low test coverage | Use prompt #5 (Testing Validation) |
| Poor documentation | Reference DOCUMENTATION_TEMPLATE.md |
| Requirements unclear | Use prompt #3 (Course Correction) |

## 🎯 Success Metrics

- ✅ Every feature has 4 documents
- ✅ Test coverage always >80%  
- ✅ Git commits are atomic
- ✅ No production bugs
- ✅ Docs actually helpful

---

**Remember**: The AI has all templates in `.aidocs/templates/`. Reference them by name when needed!

**Golden Rule**: No code without plans, no features without tests, no completion without documentation.