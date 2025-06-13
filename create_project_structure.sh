#!/bin/bash
# Script to create additional directories for the Hist_Data_Ingestor refactor.

echo "Creating supplementary directories for the Databento MVP..."

# Create top-level directories for temporary data and the Dead-Letter Queue
# as specified in the detailed design 
mkdir -p data_temp
mkdir -p dlq

# Create a subdirectory for API-specific adapters within the ingestion module.
# This aligns with the Adapter Pattern to keep Databento logic contained.
mkdir -p src/ingestion/api_adapters

# Create subdirectories for transformation rules and custom validators
# to keep mapping logic separate from validation logic. 
mkdir -p src/transformation/mapping_configs
mkdir -p src/transformation/validators

echo "Directory structure is now fully prepared."