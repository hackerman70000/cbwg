from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, Optional


class DataSource(ABC):
    """
    Abstract base class for all data sources.

    A data source is responsible for acquiring data from a specific source type and providing it in a standardized format for further processing.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the data source with optional configuration.

        Args:
            config: Optional configuration dictionary for the data source
        """
        self.config = config or {}
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """
        Validate the configuration provided to the data source.

        Raises:
            ValueError: If the configuration is invalid
        """
        pass

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the data source.

        Returns:
            bool: True if connection was successful, False otherwise

        Raises:
            ConnectionError: If connection to the source fails
        """
        pass

    @abstractmethod
    def get_data(self) -> Iterator[str]:
        """
        Retrieve data from the source.

        Returns:
            Iterator[str]: An iterator over chunks of data

        Raises:
            IOError: If data retrieval fails
        """
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the data source.

        Returns:
            Dict[str, Any]: Dictionary containing metadata about the source
        """
        pass

    def close(self) -> None:
        """
        Close the connection to the data source.

        This method should be called when done with the data source to free
        any resources.
        """
        pass

    def __enter__(self):
        """Context manager entry point."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        self.close()
