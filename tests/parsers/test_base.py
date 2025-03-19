import unittest
from unittest.mock import MagicMock

from src.parsers.base import Parser


class ConcreteParser(Parser):
    """Concrete implementation of Parser for testing purposes."""

    def _validate_config(self):
        """Implement abstract method for testing."""
        pass

    def parse(self, data):
        """Implement abstract method for testing."""
        return iter(["parsed1", "parsed2", "parsed3"])

    def get_metadata(self):
        """Implement abstract method for testing."""
        return {"parser_type": "test"}


class TestParser(unittest.TestCase):
    """Test cases for the Parser abstract base class."""

    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        parser = ConcreteParser()
        self.assertEqual({}, parser.config)

    def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        config = {"key1": "value1", "key2": "value2"}
        parser = ConcreteParser(config)
        self.assertEqual(config, parser.config)

    def test_validate_config_called_during_init(self):
        """Test that _validate_config is called during initialization."""
        ConcreteParser._validate_config = MagicMock()
        parser = ConcreteParser()
        ConcreteParser._validate_config.assert_called_once()

    def test_parse_method(self):
        """Test the parse method returns expected results."""
        parser = ConcreteParser()
        result = list(parser.parse("test data"))
        self.assertEqual(["parsed1", "parsed2", "parsed3"], result)

    def test_get_metadata_method(self):
        """Test the get_metadata method returns expected results."""
        parser = ConcreteParser()
        metadata = parser.get_metadata()
        self.assertEqual({"parser_type": "test"}, metadata)


if __name__ == "__main__":
    unittest.main()
