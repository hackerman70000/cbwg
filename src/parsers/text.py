import re
from typing import Any, Dict, Iterator, Optional

from src.parsers.base import Parser


class TextParser(Parser):
    """
    A parser that extracts words from plaintext data.

    This class handles parsing of raw text data, extracting words
    according to specified patterns and filters.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a text parser.

        Args:
            config: Optional configuration dictionary with the following options:
                - min_length: Minimum word length (default: 3)
                - max_length: Maximum word length (default: 20)
                - pattern: Regex pattern for word extraction (default: r'[a-zA-Z0-9]+')
                - include_numbers: Whether to include words with numbers (default: True)
                - preserve_case: Whether to preserve case (default: False)
                - exclude_words: List of words to exclude (default: [])
        """
        super().__init__(config)
        self.exclusion_set = set(
            word.lower() for word in self.config.get("exclude_words", [])
        )

    def _validate_config(self) -> None:
        """Validate the configuration for text parser."""

        self.config.setdefault("min_length", 3)
        self.config.setdefault("max_length", 20)
        self.config.setdefault("pattern", r"[a-zA-Z0-9]+")
        self.config.setdefault("include_numbers", True)
        self.config.setdefault("preserve_case", False)
        self.config.setdefault("exclude_words", [])

        try:
            re.compile(self.config["pattern"])
        except re.error:
            raise ValueError(f"Invalid regex pattern: {self.config['pattern']}")

        if not self.config["include_numbers"]:
            self.config["pattern"] = r"[a-zA-Z]+"

    def parse(self, data: str) -> Iterator[str]:
        """
        Parse text data to extract words.

        Args:
            data: Text data to parse

        Returns:
            Iterator[str]: An iterator over extracted words

        Raises:
            ValueError: If the data is not valid text
        """
        if not isinstance(data, str):
            raise ValueError("Input data must be a string")

        pattern = self.config["pattern"]
        min_length = self.config["min_length"]
        max_length = self.config["max_length"]
        preserve_case = self.config["preserve_case"]
        include_numbers = self.config["include_numbers"]

        for match in re.finditer(pattern, data):
            word = match.group(0)

            if not include_numbers and any(char.isdigit() for char in word):
                continue

            if min_length <= len(word) <= max_length:
                processed_word = word if preserve_case else word.lower()

                if processed_word.lower() not in self.exclusion_set:
                    yield processed_word

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the parser.

        Returns:
            Dict[str, Any]: Dictionary with parser metadata
        """
        return {
            "parser_type": "text",
            "pattern": self.config["pattern"],
            "min_length": self.config["min_length"],
            "max_length": self.config["max_length"],
            "include_numbers": self.config["include_numbers"],
            "preserve_case": self.config["preserve_case"],
            "exclude_words_count": len(self.exclusion_set),
        }
