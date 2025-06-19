# Beginner's Guide: Where Everything Goes

## 🗺️ Quick Overview - What Goes Where

### PRD (Product Requirements Document)
**Think of it as**: The "WHAT" and "WHY" document
- ✅ What we're building
- ✅ Why we're building it
- ✅ Who will use it
- ✅ High-level task breakdown
- ✅ Timeline and milestones
- ❌ NOT how to code it
- ❌ NOT git commands

### Technical Specification
**Think of it as**: The "HOW" document
- ✅ How we'll build it (architecture)
- ✅ Git workflow and branch strategy
- ✅ Detailed technical decisions
- ✅ Database design
- ✅ API design
- ✅ Which services we'll connect to
- ❌ NOT business reasons
- ❌ NOT user stories

### Test Results Document
**Think of it as**: The "PROOF" document
- ✅ Actual test outputs (copy-pasted)
- ✅ Coverage reports
- ✅ Performance test results
- ✅ Bug reports
- ❌ NOT test plans (those go in Tech Spec)
- ❌ NOT theoretical tests

### Documentation
**Think of it as**: The "HELP" document
- ✅ How to use the feature
- ✅ API examples
- ✅ Troubleshooting guides
- ✅ Setup instructions
- ❌ NOT why we built it (that's in PRD)
- ❌ NOT test results

## 📝 Task Management - Where It Goes

### Understanding the Hierarchy

```
Epic (Big Feature)
  └── Story (User-facing capability)
      └── Task (Development work)
          └── Subtask (Specific steps)
```

**Example**:
```
Epic: User Authentication System
  └── Story: As a user, I can log in with email/password
      └── Task: Build login API endpoint
          ├── Subtask: Create database schema
          ├── Subtask: Implement password hashing
          └── Subtask: Write endpoint tests
```

### In the PRD:
```markdown
### Epic E1: Authentication System
| Story ID | User Story | Priority | Points |
|----------|------------|----------|---------|
| E1-S1 | As a user, I can register an account | HIGH | 8 |
| E1-S2 | As a user, I can log in | HIGH | 5 |

#### Story E1-S1 Tasks:
| Task ID | Task Name | Hours | Dependencies |
|---------|-----------|-------|--------------|
| E1-S1-T1 | Create user model | 4 | None |
| E1-S1-T2 | Build registration API | 6 | E1-S1-T1 |
| E1-S1-T3 | Add validation | 2 | E1-S1-T2 |
```

**Why in PRD?**: Because it's about WHAT needs to be done and in what order, which is planning-level information.

### In the Tech Spec:
- Detailed implementation steps for each task
- Specific technical requirements
- Code patterns to follow

## 🌿 Git Workflow - Where It Goes

### In the Technical Specification:

#### Basic Git Flow
```bash
# 1. Start your feature
git checkout main                    # Go to main branch
git pull origin main                 # Get latest code
git checkout -b feature/add-login    # Create your feature branch

# 2. Work on your feature
# ... make changes ...
git add .                           # Stage changes
git commit -m "feat: add login form" # Commit with clear message
git push origin feature/add-login    # Push to remote

# 3. Create Pull Request
# Go to GitHub/GitLab and create PR from your branch to main
```

#### Commit Message Format
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `test:` - Adding tests
- `refactor:` - Code change that doesn't fix bug or add feature

**Why in Tech Spec?**: Because it's HOW we implement and manage code, which is technical process.

## 🔄 Common Workflow for AI Agents

### 1. **Planning Phase** (PRD)
```
1. Read requirements
2. Break down into tasks
3. Identify dependencies
4. Estimate time
```

### 2. **Technical Design** (Tech Spec)
```
1. Design architecture
2. Define git workflow
3. Plan database schema
4. Design APIs
5. Identify risks
```

### 3. **Implementation** (Code + Git)
```
1. Create feature branch
2. Implement task by task
3. Write tests for each task
4. Commit regularly
5. Update documentation
```

### 4. **Testing** (Test Results)
```
1. Run all tests
2. Copy-paste actual outputs
3. Check coverage
4. Document any failures
```

### 5. **Documentation** (Docs)
```
1. Write user guide
2. Document APIs
3. Create examples
4. Write troubleshooting guide
```

## 📋 Simple Task Tracking Example

Here's a real example of how tasks might look in your PRD:

```markdown
### Sprint 1 Tasks (Week 1-2)
| ID | Task | Description | Depends On | Status |
|----|------|-------------|------------|---------|
| 1 | Setup | Create branch, install dependencies | - | ✅ Done |
| 2 | User Model | Create user database table | 1 | ✅ Done |
| 3 | Auth API | Build login/register endpoints | 2 | 🔄 In Progress |
| 4 | Auth Tests | Write tests for auth | 3 | ⏳ Waiting |
| 5 | Auth Docs | Document auth endpoints | 3 | ⏳ Waiting |

### Dependency Chain:
Setup → User Model → Auth API → Both Tests and Docs can happen in parallel
```

## ❓ Common Questions

### Q: Where do I put my daily progress updates?
**A**: Create a `PROGRESS.md` file in your feature branch or update the PR description daily.

### Q: Where do error messages and debugging info go?
**A**: In the Test Results document under "Failed Tests Analysis" or "Debugging Log"

### Q: Where do I document configuration changes?
**A**: 
- User-facing config: Documentation (how to configure)
- Technical config: Tech Spec (why these settings)
- Config examples: Documentation

### Q: Where do performance requirements go?
**A**: 
- Business requirements ("must handle 1000 users"): PRD
- Technical requirements ("response time <200ms"): Tech Spec
- Actual results: Test Results Document

## 🚀 Quick Start Checklist for New Features

1. **Start with PRD**
   - [ ] Understand what to build
   - [ ] Break down into tasks
   - [ ] Note dependencies

2. **Move to Tech Spec**
   - [ ] Plan how to build it
   - [ ] Set up git workflow
   - [ ] Design technical architecture

3. **Begin Implementation**
   - [ ] Create feature branch
   - [ ] Follow task order from PRD
   - [ ] Commit after each task

4. **Document Everything**
   - [ ] Test results (with real output!)
   - [ ] User documentation
   - [ ] Keep PRD updated with progress

## 💡 Pro Tips for Beginners

1. **Commit Often**: Better to have too many commits than too few
2. **Write Tests First**: It helps you think about what you're building
3. **Document as You Go**: Don't wait until the end
4. **Ask for Help**: If unsure where something goes, ask!
5. **Use the Templates**: They're there to guide you

Remember: The goal is to have a clear trail of what was planned (PRD), how it was built (Tech Spec), proof it works (Test Results), and help for users (Documentation).