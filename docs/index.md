# Hist Data Ingestor Documentation

Welcome to the technical documentation for the Hist Data Ingestor project.

## Overview

This project provides a robust, modular framework for ingesting, transforming, storing, and querying historical data from multiple sources.

## Documentation Index

### **🔧 Development Process & Quality**
- **[Story Review Process](checklists/story-review-process.md)** - ⭐ **CRITICAL** - Formal 4-gate review process for all stories
- **[Story Audit Checklist](checklists/story-audit-checklist.md)** - ⭐ **CRITICAL** - Compliance audit tool for existing stories
- [Operational Guidelines](operational-guidelines.md) - Development standards and best practices
- [Contributing Guidelines](contributing.md) - Code contribution standards

### **📚 Architecture & Setup**
- [Architecture](architecture.md) - System design and component overview
- [Setup & Installation](setup.md) - Getting started guide
- [Technical Stack](tech-stack.md) - Technology choices and rationale
- [Project Structure](project_structure.md) - Codebase organization

### **📊 Data & Modules**
- [Modules](modules/)
  - [Querying Module](modules/querying.md) - Data retrieval and query functionality
  - [Storage Module](modules/storage.md) - Data persistence and TimescaleDB integration
  - [Ingestion Module](modules/ingestion.md) - Data extraction and API adapters
  - [Transformation Module](modules/transformation.md) - Data transformation and validation
- [TimescaleDB Schemas](schemas.md) - Database structure and table definitions
- [API Documentation](api/) - API reference and usage examples

### **📋 Project Management**
- [Product Requirements Document (PRD)](prd.md) - Product vision and requirements
- [Epics & Stories](epics/) - Development roadmap and user stories
- [Testing Documentation](testing/) - Test strategies and execution guides

### **🔍 Troubleshooting & Support**
- [FAQ](faq.md) - Frequently asked questions
- [Project Retrospective](project-retrospective.md) - Lessons learned and best practices
- [Integration Examples](integration-example.md) - Common integration patterns
- [Transformation Examples](transformation-examples.md) - Data transformation patterns

### **⚡ System Enhancements**
- [Crossed Markets Implementation](CROSSED_MARKETS_IMPLEMENTATION.md) - Complete crossed markets detection and flagging system
- [Crossed Markets Quick Reference](CROSSED_MARKETS_QUICK_REFERENCE.md) - Quick reference for crossed markets functionality

---

## **🚨 For New Team Members:**

**Start Here:**
1. 📖 Read [Setup & Installation](setup.md)
2. 🏗️ Review [Architecture](architecture.md) 
3. ⚠️ **MANDATORY:** Study [Story Review Process](checklists/story-review-process.md)
4. 📋 Understand [Contributing Guidelines](contributing.md)

**For Story Work:**
- ✅ **Before starting ANY story:** Follow [Story Review Process](checklists/story-review-process.md) Gate 1 & 2
- ✅ **Before marking story complete:** Use [Story Audit Checklist](checklists/story-audit-checklist.md)
- ✅ **Always follow:** [Operational Guidelines](operational-guidelines.md)