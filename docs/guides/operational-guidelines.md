# Operational Guidelines

## Coding Standards

All code must adhere to PEP 8 and be automatically formatted with Black and linted with Ruff. Type hints are mandatory for all new code, and MyPy is used for static type checking. Public modules, classes, and functions require Google-style docstrings. Dependencies must be explicitly defined and vetted before addition. Use snake_case for variables/functions, PascalCase for classes, absolute imports, and with statements for resource management. Hardcoding config values and bypassing architectural layers is forbidden.

## Error Handling

- Use tenacity for retrying transient API/network errors with exponential backoff and respect Retry-After headers.
- Log all errors using structlog in structured JSON format.
- Persistent failures after retries are routed to a Dead-Letter Queue (DLQ) for later inspection.
- Database writes are atomic; failed batches are rolled back and sent to the DLQ.
- Data transformation/validation errors result in quarantined records, but the pipeline continues processing valid data.

## Security

- API keys, DB credentials, and other secrets must not be hardcoded or committed; load from environment variables or a .env file (git-ignored).
- All external data is validated with Pydantic models; CLI inputs are validated by Typer.
- Dependencies are regularly scanned for vulnerabilities (e.g., pip-audit) and kept up to date.
- Internal error details are logged, not shown to users; CLI displays only generic error messages.
- Database users should have only necessary permissions (principle of least privilege).

## Testing Strategy

- Use PyTest as the primary testing framework; mock external dependencies with unittest.mock or pytest-mock.
- Unit tests are required for all critical logic, especially transformation, validation, and storage. Place in tests/unit/ mirroring src/ structure.
- Integration tests verify component interactions and pipeline flow for small datasets; test live API and DB connectivity in Docker.
- End-to-end tests are out of scope for MVP, but manual CLI-driven validation is required for key scenarios.
- Store static test data in tests/fixtures/ for consistent, repeatable tests. 