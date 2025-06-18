"""
Transformation mapping configurations for different data providers.

This package contains YAML configuration files that define how to map
data provider-specific models to standardized internal schemas.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any

# Package metadata
__version__ = "1.0.0"
__author__ = "hist_data_ingestor"


def load_databento_mappings() -> Dict[str, Any]:
    """
    Load Databento mapping configuration from YAML file.

    Returns:
        Dict containing the databento mappings configuration
    """
    config_path = Path(__file__).parent / "databento_mappings.yaml"

    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)


def load_mapping_config(provider: str) -> Dict[str, Any]:
    """
    Load mapping configuration for a specific data provider.

    Args:
        provider: Data provider name (e.g., 'databento', 'interactive_brokers')

    Returns:
        Dict containing the mapping configuration

    Raises:
        FileNotFoundError: If mapping file doesn't exist
        ValueError: If provider is not supported
    """
    supported_providers = ["databento", "interactive_brokers"]

    if provider not in supported_providers:
        raise ValueError(f"Provider '{provider}' not supported. Supported: {supported_providers}")

    config_path = Path(__file__).parent / f"{provider}_mappings.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Mapping config not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)


# Convenience imports for common mappings
try:
    databento_mappings = load_databento_mappings()
except Exception as e:
    # Graceful fallback if YAML loading fails
    databento_mappings = None
    print(f"Warning: Could not load databento mappings: {e}")

__all__ = [
    "load_databento_mappings",
    "load_mapping_config",
    "databento_mappings"
]
