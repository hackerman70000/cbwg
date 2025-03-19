import unittest

from src.parsers.text import TextParser


class TestTextParser(unittest.TestCase):
    """Test cases for the TextParser class."""

    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        parser = TextParser()
        self.assertEqual(3, parser.config["min_length"])
        self.assertEqual(20, parser.config["max_length"])
        self.assertEqual(r"[a-zA-Z0-9]+", parser.config["pattern"])
        self.assertTrue(parser.config["include_numbers"])
        self.assertFalse(parser.config["preserve_case"])
        self.assertEqual([], parser.config["exclude_words"])
        self.assertEqual(set(), parser.exclusion_set)

    def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        config = {
            "min_length": 5,
            "max_length": 15,
            "pattern": r"[a-zA-Z]+",
            "include_numbers": False,
            "preserve_case": True,
            "exclude_words": ["test", "example"],
        }
        parser = TextParser(config)
        self.assertEqual(5, parser.config["min_length"])
        self.assertEqual(15, parser.config["max_length"])
        self.assertEqual(r"[a-zA-Z]+", parser.config["pattern"])
        self.assertFalse(parser.config["include_numbers"])
        self.assertTrue(parser.config["preserve_case"])
        self.assertEqual(["test", "example"], parser.config["exclude_words"])
        self.assertEqual({"test", "example"}, parser.exclusion_set)

    def test_validate_config_with_invalid_pattern(self):
        """Test validation with invalid regex pattern."""
        with self.assertRaises(ValueError):
            TextParser({"pattern": r"[a-zA-Z++"})  # Invalid regex

    def test_parse_basic_text(self):
        """Test parsing basic text with default settings."""
        parser = TextParser()
        text = "This is a simple test with some numbers 123 and words."
        words = list(parser.parse(text))

        # Default settings: min_length=3, include_numbers=True, preserve_case=False
        expected = [
            "this",
            "simple",
            "test",
            "with",
            "some",
            "numbers",
            "123",
            "and",
            "words",
        ]
        self.assertEqual(expected, words)

    def test_parse_with_length_filters(self):
        """Test parsing with custom length filters."""
        parser = TextParser({"min_length": 5, "max_length": 7})
        text = "Short and longer words with some very long terminology"
        words = list(parser.parse(text))

        # Note: "with" has only 4 characters, so it doesn't meet the min_length=5 requirement
        expected = ["short", "longer", "words"]
        self.assertEqual(expected, words)

    def test_parse_exclude_numbers(self):
        """Test parsing with numbers excluded."""
        parser = TextParser({"include_numbers": False})
        text = "Text with num3ric parts and pure123numbers and plain text."
        words = list(parser.parse(text))

        # When include_numbers=False, the pattern is changed to only match alphabetic characters
        # This means "num3ric" will be split into "num" and "ric", and "pure123numbers" into "pure" and "numbers"
        expected = [
            "text",
            "with",
            "num",
            "ric",
            "parts",
            "and",
            "pure",
            "numbers",
            "and",
            "plain",
            "text",
        ]
        self.assertEqual(expected, words)

    def test_parse_preserve_case(self):
        """Test parsing with case preservation."""
        parser = TextParser({"preserve_case": True})
        text = "Mixed UPPER lower CamelCase words."
        words = list(parser.parse(text))

        # Case should be preserved
        expected = ["Mixed", "UPPER", "lower", "CamelCase", "words"]
        self.assertEqual(expected, words)

    def test_parse_excluded_words(self):
        """Test parsing with excluded words."""
        parser = TextParser({"exclude_words": ["test", "example", "sample"]})
        text = "This is a test example with sample words and others."
        words = list(parser.parse(text))

        # Excluded words should not be included
        expected = ["this", "with", "words", "and", "others"]
        self.assertEqual(expected, words)

    def test_parse_custom_pattern(self):
        """Test parsing with a custom pattern."""
        parser = TextParser(
            {"pattern": r"[a-zA-Z]{4,}"}
        )  # Only alphabetic words with 4+ chars
        text = "This is a test with some special-characters and numbers123."
        words = list(parser.parse(text))

        # Only words matching the pattern should be included
        expected = ["this", "test", "with", "some", "special", "characters", "numbers"]
        self.assertEqual(expected, words)

    def test_parse_invalid_input(self):
        """Test parsing with invalid input."""
        parser = TextParser()
        with self.assertRaises(ValueError):
            list(parser.parse(None))  # None is not a valid string

        with self.assertRaises(ValueError):
            list(parser.parse(123))  # Integer is not a valid string

    def test_get_metadata(self):
        """Test getting parser metadata."""
        config = {
            "min_length": 4,
            "max_length": 10,
            "include_numbers": False,
            "exclude_words": ["one", "two", "three"],
        }
        parser = TextParser(config)
        metadata = parser.get_metadata()

        self.assertEqual("text", metadata["parser_type"])
        self.assertEqual(4, metadata["min_length"])
        self.assertEqual(10, metadata["max_length"])
        self.assertEqual(r"[a-zA-Z]+", metadata["pattern"])  # Pattern should be updated
        self.assertFalse(metadata["include_numbers"])
        self.assertFalse(metadata["preserve_case"])
        self.assertEqual(3, metadata["exclude_words_count"])


if __name__ == "__main__":
    unittest.main()
