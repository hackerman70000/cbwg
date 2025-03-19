import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line("markers", "sources: tests for data sources")
    config.addinivalue_line("markers", "parsers: tests for parsers")


def pytest_collection_modifyitems(items):
    """Add markers to test items based on module path."""
    for item in items:
        if "sources" in item.nodeid:
            item.add_marker(pytest.mark.sources)
        elif "parsers" in item.nodeid:
            item.add_marker(pytest.mark.parsers)
