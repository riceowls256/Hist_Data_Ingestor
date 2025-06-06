#!/bin/bash

# Create main directories
mkdir -p hist_data_ingestor/.claude
mkdir -p hist_data_ingestor/.github/workflows
mkdir -p hist_data_ingestor/.vscode
mkdir -p hist_data_ingestor/ai-docs
mkdir -p hist_data_ingestor/build
mkdir -p hist_data_ingestor/configs/api_specific
mkdir -p hist_data_ingestor/configs/validation_schemas
mkdir -p hist_data_ingestor/docs
mkdir -p hist_data_ingestor/infra
mkdir -p hist_data_ingestor/logs
mkdir -p hist_data_ingestor/specs
mkdir -p hist_data_ingestor/venv
mkdir -p hist_data_ingestor/src/core
mkdir -p hist_data_ingestor/src/ingestion/api_adapters
mkdir -p hist_data_ingestor/src/transformation/rule_engine
mkdir -p hist_data_ingestor/src/transformation/mapping_configs
mkdir -p hist_data_ingestor/src/transformation/validators
mkdir -p hist_data_ingestor/src/storage
mkdir -p hist_data_ingestor/src/querying
mkdir -p hist_data_ingestor/src/cli
mkdir -p hist_data_ingestor/src/utils
mkdir -p hist_data_ingestor/tests/fixtures
mkdir -p hist_data_ingestor/tests/unit/core
mkdir -p hist_data_ingestor/tests/unit/ingestion
mkdir -p hist_data_ingestor/tests/integration

# Create example files
touch hist_data_ingestor/.github/workflows/main.yml
touch hist_data_ingestor/.vscode/settings.json
touch hist_data_ingestor/configs/system_config.yaml
touch hist_data_ingestor/configs/api_specific/interactive_brokers_config.yaml
touch hist_data_ingestor/configs/api_specific/databento_config.yaml
touch hist_data_ingestor/configs/validation_schemas/ib_raw_schema.json
touch hist_data_ingestor/configs/validation_schemas/databento_raw_schema.json
touch hist_data_ingestor/docs/index.md
touch hist_data_ingestor/docs/prd.md
touch hist_data_ingestor/docs/architecture.md
touch hist_data_ingestor/infra/docker-compose.yml
touch hist_data_ingestor/logs/app.log
touch hist_data_ingestor/src/__init__.py
touch hist_data_ingestor/src/core/__init__.py
touch hist_data_ingestor/src/core/pipeline_orchestrator.py
touch hist_data_ingestor/src/core/config_manager.py
touch hist_data_ingestor/src/core/module_loader.py
touch hist_data_ingestor/src/ingestion/__init__.py
touch hist_data_ingestor/src/ingestion/api_adapters/__init__.py
touch hist_data_ingestor/src/ingestion/api_adapters/base_adapter.py
touch hist_data_ingestor/src/ingestion/api_adapters/interactive_brokers_adapter.py
touch hist_data_ingestor/src/ingestion/api_adapters/databento_adapter.py
touch hist_data_ingestor/src/ingestion/data_fetcher.py
touch hist_data_ingestor/src/transformation/__init__.py
touch hist_data_ingestor/src/transformation/rule_engine/__init__.py
touch hist_data_ingestor/src/transformation/rule_engine/engine.py
touch hist_data_ingestor/src/transformation/mapping_configs/interactive_brokers_mappings.yaml
touch hist_data_ingestor/src/transformation/mapping_configs/databento_mappings.yaml
touch hist_data_ingestor/src/transformation/validators/__init__.py
touch hist_data_ingestor/src/transformation/validators/data_validator.py
touch hist_data_ingestor/src/storage/__init__.py
touch hist_data_ingestor/src/storage/timescale_loader.py
touch hist_data_ingestor/src/storage/models.py
touch hist_data_ingestor/src/querying/__init__.py
touch hist_data_ingestor/src/querying/query_builder.py
touch hist_data_ingestor/src/cli/__init__.py
touch hist_data_ingestor/src/cli/commands.py
touch hist_data_ingestor/src/utils/__init__.py
touch hist_data_ingestor/src/utils/custom_logger.py
touch hist_data_ingestor/src/main.py
touch hist_data_ingestor/tests/__init__.py
touch hist_data_ingestor/tests/fixtures/.gitkeep
touch hist_data_ingestor/tests/unit/core/.gitkeep
touch hist_data_ingestor/tests/unit/ingestion/.gitkeep
touch hist_data_ingestor/tests/integration/test_data_pipeline.py
touch hist_data_ingestor/.env.example
touch hist_data_ingestor/.gitignore
touch hist_data_ingestor/requirements.txt
touch hist_data_ingestor/pyproject.toml
touch hist_data_ingestor/Dockerfile
touch hist_data_ingestor/README.md

echo "Directory structure created."