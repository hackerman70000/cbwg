from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional


class Transformer(ABC):
    """
    Abstract base class for all word transformers.

    A transformer takes input words and applies transformations to generate
    new candidate words for the wordlist.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the transformer with optional configuration.

        Args:
            config: Optional configuration dictionary for the transformer
        """
        self.config = config or {}
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """
        Validate the configuration provided to the transformer.

        Raises:
            ValueError: If the configuration is invalid
        """
        pass

    @abstractmethod
    def transform(self, words: List[str]) -> Iterator[str]:
        """
        Transform input words to generate new candidate words.

        Args:
            words: List of input words to transform

        Returns:
            Iterator[str]: An iterator over transformed words

        Raises:
            ValueError: If the transformation cannot be performed
        """
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the transformer.

        Returns:
            Dict[str, Any]: Dictionary containing metadata about the transformer
        """
        pass
