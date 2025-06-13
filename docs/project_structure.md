# Project Structure

The project structure is a physical manifestation of the architecture, designed to enforce a clean separation of concerns and promote modularity. The following idealized structure serves as the blueprint for the repository, providing a clear and scalable organization for source code, configuration, documentation, and tests. Adhering to this structure is essential for maintaining code quality and combating entropy as the project evolves.

.
├── ai-docs/                        # AI agent documentation and persona files
├── build/                          # Build artifacts or scripts (if used)
├── configs/                        # Configuration files for the project
│   ├── api_specific/               # API-specific config files (e.g., for Databento, IB)
│   ├── system_config.yaml          # Main system configuration (YAML)
│   └── validation_schemas/         # JSON schemas for validating data
├── data_temp/                      # Temporary data storage (if used)
├── dlq/                            # Dead-letter queue or error data (if used)
├── docs/                           # Project documentation
│   ├── api/                        # API documentation
│   ├── architecture.md             # System architecture overview
│   ├── contributing.md             # Contribution guidelines
│   ├── epics/                      # Epic-level documentation
│   ├── faq.md                      # Frequently asked questions
│   ├── index.md                    # Docs index/landing page
│   ├── modules/                    # Module-level documentation
│   ├── prd.md                      # Product requirements document
│   ├── project-retrospective.md    # Lessons learned and retrospectives
│   ├── setup.md                    # Setup instructions
│   └── stories/                    # User stories and story files
│       ├── 1.1.story.md            # Story 1.1: Project initialization
│       ├── 1.2.story.md            # Story 1.2: Config management
│       ├── 1.3.story.md            # Story 1.3: Docker environment
│       └── 1.4.story.md            # Story 1.4: Centralized logging
├── infra/                          # Infrastructure-as-code or deployment scripts
├── logs/                           # Application and test log files
│   ├── app.log                     # Main application log
│   ├── test_app.log                # Log file for tests
│   └── test_console.log            # Console log for tests
├── specs/                          # Technical specifications (if used)
├── src/                            # Main source code
│   ├── __init__.py                 # Marks src as a Python package
│   ├── __pycache__/                # Python bytecode cache
│   ├── cli/                        # Command-line interface code
│   │   ├── __init__.py
│   │   └── commands.py
│   ├── core/                       # Core system modules (e.g., config, orchestrator)
│   │   ├── __init__.py
│   │   ├── config_manager.py       # Configuration manager implementation
│   │   ├── module_loader.py        # Module loading logic
│   │   └── pipeline_orchestrator.py# Pipeline orchestration logic
│   ├── hist_data_ingestor.egg-info/# Package metadata (if installed as a package)
│   │   ├── dependency_links.txt
│   │   ├── PKG-INFO
│   │   ├── SOURCES.txt
│   │   └── top_level.txt
│   ├── ingestion/                  # Data ingestion logic
│   │   ├── __init__.py
│   │   ├── api_adapters/           # API adapter modules
│   │   └── data_fetcher.py         # Data fetching logic
│   ├── main.py                     # Main entry point (if used)
│   ├── querying/                   # Querying logic
│   │   ├── __init__.py
│   │   └── query_builder.py
│   ├── storage/                    # Data storage logic
│   │   ├── __init__.py
│   │   ├── models.py               # Data models
│   │   └── timescale_loader.py     # TimescaleDB loader
│   ├── transformation/             # Data transformation logic
│   │   ├── __init__.py
│   │   ├── mapping_configs/        # Mapping configuration files
│   │   ├── rule_engine/            # Rule engine logic
│   │   └── validators/             # Data validators
│   └── utils/                      # Utility modules
│       ├── __init__.py
│       └── custom_logger.py        # Centralized logging setup
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── __pycache__/
│   ├──.DS_Store
│   ├── fixtures/                   # Test fixtures
│   │   └──.gitkeep
│   ├── integration/                # Integration tests
│   │   └── test_data_pipeline.py
│   ├── unit/                       # Unit tests
│   │   ├── __init__.py
│   │   ├── core/
│   │   └── ingestion/
│   └── utils/                      # Utility tests
│       └── test_custom_logger.py   # Logger unit tests
├── venv/                           # Python virtual environment
├──.claude/                        # Claude AI config (if used)
├──.DS_Store                       # macOS system file
├──.env                            # Environment variables (not committed)
├──.git/                           # Git version control
├──.gitignore                      # Git ignore rules
├──.pytest_cache/                  # Pytest cache
├──.vscode/                        # VSCode editor settings
│   └── settings.json
├── create_project_structure.sh     # Script to create project structure
├── docker-compose.yml              # Docker Compose config
├── Dockerfile                      # Docker build file
├── ide-bmad-orchestrator.cfg.md    # BMAD orchestrator config (relative paths)
├── ide-bmad-orchestrator.md        # BMAD orchestrator main doc
├── pyproject.toml                  # Python project metadata/config
├── README.md                       # Project overview and instructions
├── requirements.txt                # Python dependencies
