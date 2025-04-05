import logging
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.transformers.rules import RuleTransformer
from src.utils.env import find_project_root, load_environment

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_environment()
project_root = find_project_root()


class TestRuleTransformer(unittest.TestCase):
    """Test suite for the Rule transformer module."""

    @classmethod
    def setUpClass(cls):
        cls.output_dir = project_root / "tests" / "output"
        cls.output_dir.mkdir(exist_ok=True)

        for file in cls.output_dir.glob("*"):
            try:
                file.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete {file}: {e}")

        logger.info(f"Cleaned and prepared output directory at {cls.output_dir}")
        cls.sample_words = ["password", "security", "authentication", "123456"]

    def setUp(self):
        self.rules_dir = project_root / "tests" / "output" / "resources" / "rules"
        self.rules_dir.mkdir(exist_ok=True, parents=True)
        self.test_rule_path = self._create_test_rule_file()
        self.mock_transformed = [
            "password1", "PASSWORD", "p@ssw0rd", 
            "security1", "SECURITY", "s3cur1ty",
            "authentication1", "AUTHENTICATION", "auth3nt1c4t10n",
            "1234561", "123456!", "12345678"
        ]

    def _create_test_rule_file(self):
        """Create a test rule file for testing."""
        test_rule_file = self.rules_dir / "test.rule"
        
        with open(test_rule_file, "w") as f:
            f.write("$1\n")  # Add '1' at the end
            f.write("T\n")   # Toggle case (uppercase)
            f.write("sa@\n") # Substitute 'a' with '@'
            f.write("se3\n") # Substitute 'e' with '3'
            f.write("si1\n") # Substitute 'i' with '1'
            f.write("so0\n") # Substitute 'o' with '0'
        
        logger.info(f"Created test rule file at {test_rule_file}")
        return test_rule_file

    @patch("src.transformers.rules.hashcat_run")
    def test_rule_transformer_initialization(self, mock_hashcat_run):
        """Test that the rule transformer initializes correctly."""
        transformer = RuleTransformer(
            config={
                "rules_path": str(self.rules_dir),
                "batch_size": 5000,
                "verbose_logging": True
            }
        )

        self.assertEqual(transformer.config["rules_path"], str(self.rules_dir))
        self.assertEqual(transformer.config["batch_size"], 5000)
        self.assertTrue(transformer.config["verbose_logging"])
        self.assertTrue(len(transformer.rules) > 0)

    def test_initialization_with_missing_rules_path(self):
        """Test initialization with missing rules path raises error."""
        with self.assertRaises(ValueError):
            RuleTransformer(config={"rules_path": "", "rules": []})

    def test_initialization_with_nonexistent_path(self):
        """Test initialization with non-existent path raises error."""
        with self.assertRaises(FileNotFoundError):
            RuleTransformer(config={"rules_path": "/path/does/not/exist"})

    def test_initialization_with_custom_rules(self):
        """Test initialization with custom rules."""
        custom_rules = ["$1", "T", "sa@"]
        transformer = RuleTransformer(
            config={
                "rules_path": str(self.rules_dir),
                "rules": custom_rules
            }
        )
        
        # The rules should include both file rules and custom rules
        self.assertTrue(len(transformer.rules) > len(custom_rules))
        for rule in custom_rules:
            self.assertIn(rule, transformer.rules)

    @patch("src.transformers.rules.hashcat_run")
    def test_transform_with_mock(self, mock_hashcat_run):
        """Test transformation using mocked hashcat_run function."""
        mock_hashcat_run.return_value = self.mock_transformed

        transformer = RuleTransformer(
            config={
                "rules_path": str(self.rules_dir),
                "batch_size": 1000,
            }
        )

        result = list(transformer.transform(self.sample_words))

        mock_hashcat_run.assert_called_once()
        args, kwargs = mock_hashcat_run.call_args
        self.assertEqual(kwargs["words"], self.sample_words)
        self.assertEqual(len(result), len(self.mock_transformed))
        self.assertIn("p@ssw0rd", result)
        self.assertIn("s3cur1ty", result)

    @patch("src.transformers.rules.hashcat_run")
    def test_transform_empty_input(self, mock_hashcat_run):
        """Test transformation with empty input."""
        transformer = RuleTransformer(
            config={
                "rules_path": str(self.rules_dir),
            }
        )

        result = list(transformer.transform([]))
        self.assertEqual(result, [])
        mock_hashcat_run.assert_not_called()

    @patch("src.transformers.rules.hashcat_run")
    def test_validation_of_input_words(self, mock_hashcat_run):
        """Test validation of input words."""
        transformer = RuleTransformer(
            config={
                "rules_path": str(self.rules_dir),
            }
        )

        with self.assertRaises(ValueError):
            list(transformer.transform(["valid", 123]))  # Non-string input

        mock_hashcat_run.assert_not_called()

    @patch("src.transformers.rules.hashcat_run")
    def test_batch_processing(self, mock_hashcat_run):
        """Test batch processing functionality."""
        # Setup mock to return different values for different batches
        mock_hashcat_run.side_effect = [
            ["password1", "PASSWORD", "p@ssw0rd"],
            ["security1", "SECURITY"]
        ]

        transformer = RuleTransformer(
            config={
                "rules_path": str(self.rules_dir),
                "batch_size": 2  # Set small batch size to test batching
            }
        )

        result = list(transformer.transform(self.sample_words))
        
        # Should be called twice because batch_size = 2 and we have 4 sample words
        self.assertEqual(mock_hashcat_run.call_count, 2)
        self.assertEqual(len(result), 5)  # Total from both batches

    def test_get_metadata(self):
        """Test the get_metadata method."""
        transformer = RuleTransformer(
            config={
                "rules_path": str(self.rules_dir),
                "batch_size": 5000,
            }
        )

        metadata = transformer.get_metadata()
        self.assertEqual(metadata["transformer_type"], "rule")
        self.assertEqual(metadata["rules_path"], str(self.rules_dir))
        self.assertEqual(metadata["batch_size"], 5000)


if __name__ == "__main__":
    unittest.main()
