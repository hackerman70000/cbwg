import unittest
from unittest.mock import MagicMock

from src.sources.base import DataSource


class ConcreteDataSource(DataSource):
    """Concrete implementation of DataSource for testing purposes."""

    def _validate_config(self):
        """Implement abstract method for testing."""
        pass

    def connect(self):
        """Implement abstract method for testing."""
        return True

    def get_data(self):
        """Implement abstract method for testing."""
        return iter(["test1", "test2", "test3"])

    def get_metadata(self):
        """Implement abstract method for testing."""
        return {"source_type": "test"}


class TestDataSource(unittest.TestCase):
    """Test cases for the DataSource abstract base class."""

    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        source = ConcreteDataSource()
        self.assertEqual({}, source.config)

    def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        config = {"key1": "value1", "key2": "value2"}
        source = ConcreteDataSource(config)
        self.assertEqual(config, source.config)

    def test_context_manager(self):
        """Test using the data source as a context manager."""
        # Create a mock to verify connect and close are called
        source = ConcreteDataSource()
        source.connect = MagicMock(return_value=True)
        source.close = MagicMock()

        with source as ds:
            # Verify connect was called
            source.connect.assert_called_once()
            self.assertEqual(source, ds)

            # Test getting data within the context
            data = list(ds.get_data())
            self.assertEqual(["test1", "test2", "test3"], data)

        # Verify close was called after exiting the context
        source.close.assert_called_once()

    def test_close_method(self):
        """Test the default close method."""
        source = ConcreteDataSource()
        # The default implementation should not raise exceptions
        source.close()


if __name__ == "__main__":
    unittest.main()
