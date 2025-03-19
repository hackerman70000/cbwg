from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, Optional


class Parser(ABC):
    """
    Abstract base class for all data parsers.

    A parser is responsible for extracting words or phrases from raw data,
    converting it into a standardized format that can be processed by the
    wordlist generator.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the parser with optional configuration.

        Args:
            config: Optional configuration dictionary for the parser
        """
        self.config = config or {}
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """
        Validate the configuration provided to the parser.

        Raises:
            ValueError: If the configuration is invalid
        """
        pass

    @abstractmethod
    def parse(self, data: str) -> Iterator[str]:
        """
        Parse raw data to extract words or phrases.

        Args:
            data: Raw data to parse

        Returns:
            Iterator[str]: An iterator over extracted words or phrases

        Raises:
            ValueError: If the data cannot be parsed
        """
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the parser.

        Returns:
            Dict[str, Any]: Dictionary containing metadata about the parser
        """
        pass
