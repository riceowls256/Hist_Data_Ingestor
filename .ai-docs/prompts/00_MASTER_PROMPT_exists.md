# AI Project Initialization - Master Prompt

## Initial Context Loading

Before we begin any work, you need to understand our complete development workflow and standards. Please read and internalize all documentation in the following order:

### Phase 1: Understanding the Workflow (Read First)

1. **Start with the overview**:
   ```
   Read: .aidocs/templates/BEGINNERS_GUIDE_WHERE_EVERYTHING_GOES.md
   ```
   This explains what information goes in which document and why.

2. **Understand your responsibilities**:
   ```
   Read: .aidocs/templates/AI_AGENT_CHECKLIST.md
   ```
   This is your step-by-step guide for every feature. You must follow this checklist exactly.

3. **Learn the workflow**:
   ```
   Read: AI_WORKFLOW_README.md (in project root)
   ```
   This explains the complete development process.

### Phase 2: Document Templates (Read Second)

Read each template in this order to understand what you'll be creating:

4. **Product Requirements Document**:
   ```
   Read: .aidocs/templates/PRD_TEMPLATE.md
   ```
   Version 2.0 - Includes Epic→Story→Task→Subtask hierarchy

5. **Technical Specification**:
   ```
   Read: .aidocs/templates/TECH_SPEC_TEMPLATE.md
   ```
   Version 4.0 - Includes git workflow and risk analysis

6. **Test Results Document**:
   ```
   Read: .aidocs/templates/TEST_RESULTS_TEMPLATE.md
   ```
   Version 1.0 - You must paste ACTUAL test outputs here

7. **Documentation Template**:
   ```
   Read: .aidocs/templates/DOCUMENTATION_TEMPLATE.md
   ```
   Version 1.0 - User guides, API docs, troubleshooting

### Phase 3: Review Process (Read Third)

8. **How your work will be reviewed**:
   ```
   Read: .aidocs/templates/AI_WORK_REVIEW_TEMPLATE.md
   ```
   Understand how humans will evaluate your work.

### Phase 4: Prompt Templates (Reference)

9. **Available prompts**:
   ```
   Read: .aidocs/prompts/README.md
   ```
   This index explains when each prompt is used.

10. **Project kickoff prompt**:
    ```
    Read: .aidocs/prompts/01_PROJECT_KICKOFF.md
    ```
    This is the template for starting new features.

### Phase 5: Project Context (Read Last)

11. **Project structure**:
    ```
    Read: README.md (in project root)
    ```
    Understand the project setup and structure.

12. **Quick reference**:
    ```
    Read: AI_WORKFLOW_QUICK_START_CHEATSHEET.md
    ```
    Keep this handy for quick lookups.

## Confirmation Required

After reading all documents, please confirm your understanding by:

1. **Summarizing the 4 documents** you must create for every feature
2. **Listing the key phases** of development (Planning → Development → Testing → Completion)
3. **Stating the minimum test coverage** requirement (80%)
4. **Explaining what goes in each document**:
   - PRD contains: [your summary]
   - Tech Spec contains: [your summary]
   - Test Results contains: [your summary]
   - Documentation contains: [your summary]
5. **Confirming you understand** that you must:
   - Use context7 MCP server for code standards
   - Paste actual test outputs, not summaries
   - Follow TDD (write tests first)
   - Document all design decisions with reasoning

## Project Standards to Remember

### Critical Requirements
- **NO SHORTCUTS**: Quality over speed
- **EVIDENCE BASED**: Always paste actual command outputs
- **DOCUMENTATION FIRST**: Plan before coding
- **TEST DRIVEN**: Write tests before implementation
- **ATOMIC COMMITS**: One logical change per commit
- **ERROR HANDLING**: Every function must handle errors
- **LOGGING**: Use structlog throughout (if applicable)

### Git Workflow
- Create feature branch from main
- Use conventional commits (feat:, fix:, docs:, test:)
- Never push directly to main
- Include ticket numbers in commits

### Code Quality
- Follow existing patterns (check with context7 MCP)
- All functions need docstrings
- Complex logic needs comments
- No TODO comments in final code
- No debug print statements

## Ready to Begin?

Once you've read all documents and confirmed your understanding, I'll provide you with your first task using the PROJECT_KICKOFF prompt template.

Do you confirm that you have:
1. Read all 12 documents listed above?
2. Understand the workflow and requirements?
3. Are ready to follow the AI_AGENT_CHECKLIST for all work?

Please provide the confirmation summary requested above.