# Definitive Tech Stack Selections

This table provides a single source of truth for the project's technology landscape. Every tool is chosen for a clear purpose and to prevent dependency creep.

| Category           | Technology         | Version / Details   | Description / Purpose                                 | Justification                                                      |
|--------------------|-------------------|---------------------|------------------------------------------------------|--------------------------------------------------------------------|
| Languages          | Python            | 3.11.x              | Core language for the entire application              | Mandated by project requirements; excellent for data processing     |
| Containerization   | Docker            | Latest Stable       | Reproducible application containers                   | Standard for consistent deployment and local development            |
|                    | Docker Compose    | Latest Stable       | Orchestrate local multi-container environment         | Simplifies local setup of the application and database              |
| Database           | TimescaleDB       | Latest Stable       | Primary time-series database                          | Mandated; optimized for time-series data, based on PostgreSQL       |
|                    | SQLAlchemy        | 2.0.x               | Core database toolkit and ORM                         | For interacting with TimescaleDB in a Pythonic way                  |
|                    | psycopg2-binary   | >=2.9.5             | PostgreSQL adapter for Python                         | Required for SQLAlchemy to connect to PostgreSQL                    |
| Configuration      | YAML              | N/A                 | Format for configuration files                        | Human-readable and good for structured data                         |
|                    | Pydantic          | >=2.5.0             | Data validation and settings management               | For parsing/validating YAML configs and API responses               |
|                    | pydantic-settings | >=2.1.0             | Load Pydantic models from env vars/files              | Works with Pydantic for layered configuration                       |
| API Interaction    | databento-python  | >=0.52.0            | Official Python client for Databento API              | Official library for Databento data ingestion                       |
|                    | tenacity          | >=8.2.0             | General-purpose retrying library                      | For robust API call retries with exponential backoff                |
| Data Handling      | Pandas            | >=2.0.0             | Data analysis and manipulation library                | Used with Pandera and for general data processing                   |
|                    | Pandera           | Latest Stable       | Data validation for Pandas DataFrames                 | For post-transformation data quality checks                         |
| CLI Development    | Typer             | Latest Stable       | Build Command Line Interfaces                         | For creating a modern, user-friendly CLI                            |
| Logging            | structlog         | >=23.0.0            | Advanced structured logging for Python                | For flexible, context-aware, structured JSON logging                |
| Linting/Formatting | Ruff / Black      | Latest Stable       | Enforce code style and quality standards              | Ruff is a modern, high-performance linter; Black is the formatter   |
|                    | MyPy              | Latest Stable       | Optional static type checker for Python               | For enforcing type safety and catching bugs early                   |
| Documentation      | Sphinx            | Latest Stable       | Generate HTML documentation from code                 | Standard tool for professional Python project documentation         |
|                    | MyST Parser       | Latest Stable       | Sphinx extension for Markdown support                 | Allows writing documentation in Markdown for ease of use            |