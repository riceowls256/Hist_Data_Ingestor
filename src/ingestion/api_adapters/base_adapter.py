"""
Base adapter class for all API data adapters.

This module provides the abstract base class that all API adapters must inherit from,
ensuring a consistent interface across different data providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional
from pydantic import BaseModel


class BaseAdapter(ABC):
    """
    Abstract base class for all API data adapters.

    This class defines the common interface that all API adapters must implement
    to ensure consistency across different data providers (Databento, Interactive Brokers, etc.).
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the adapter with configuration.

        Args:
            config: Configuration dictionary containing API credentials and settings
        """
        self.config = config
        self._client: Optional[Any] = None

    @abstractmethod
    def connect(self) -> None:
        """
        Establish connection to the API.

        Raises:
            ConnectionError: If connection cannot be established
        """
        pass

    @abstractmethod
    def fetch_historical_data(self, job_config: Dict[str, Any]) -> Iterator[BaseModel]:
        """
        Fetch historical data based on job configuration.

        Args:
            job_config: Job configuration containing dataset, schema, symbols, date range, etc.

        Yields:
            BaseModel: Validated Pydantic model instances containing the fetched data

        Raises:
            ValueError: If job configuration is invalid
            ConnectionError: If API connection fails
            RuntimeError: If data fetching fails
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate the adapter configuration.

        Returns:
            bool: True if configuration is valid, False otherwise
        """
        pass

    def disconnect(self) -> None:
        """
        Close connection to the API.

        Default implementation does nothing. Override if cleanup is needed.
        """
        pass

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
