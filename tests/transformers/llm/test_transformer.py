import json
import logging
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Try to find and load .env file
project_root = Path(__file__).resolve().parent.parent.parent.parent
env_path = project_root / ".env"
if env_path.exists():
    logger.info(f"Loading environment variables from {env_path}")
    load_dotenv(env_path)
else:
    logger.warning(f"No .env file found at {env_path}")

# Import the necessary modules
try:
    from src.transformers.llm.client import GoogleAIClient
    from src.transformers.llm.transformer import LLMTransformer
except ImportError:
    logger.error(
        "Failed to import required modules. Make sure the project structure is correct."
    )
    raise


class TestLLMTransformer(unittest.TestCase):
    """Test suite for the LLM transformer module."""

    @classmethod
    def setUpClass(cls):
        """Set up class-level fixtures."""
        # Define the output directory
        cls.output_dir = project_root / "tests" / "output"
        cls.output_dir.mkdir(exist_ok=True)
        logger.info(f"Created output directory at {cls.output_dir}")

        # Define sample words
        cls.sample_words = ["password", "security", "authentication", "123456"]

    def setUp(self):
        """Set up test fixtures before each test method is run."""
        # Check if API key is available
        self.api_key = os.environ.get("GOOGLE_API_KEY")

        # Path to the prompt template
        self.prompt_path = (
            project_root / "resources" / "prompts" / "wordlist-generation.md"
        )
        if not self.prompt_path.exists():
            logger.warning(f"Prompt template not found at {self.prompt_path}")

            # For testing, we'll create a temporary test prompt file
            self.test_prompt_path = self.output_dir / "test_prompt.md"
            self._create_test_prompt(self.test_prompt_path)
            logger.info(f"Created test prompt at {self.test_prompt_path}")
            self.prompt_path = self.test_prompt_path

        # Sample mock response
        self.mock_response = ["p@ssw0rd", "s3curity", "auth123", "password123"]

    def _create_test_prompt(self, path):
        """Create a simple test prompt at the specified path."""
        prompt_content = (
            "# Test Prompt\n\nGenerate variations of the input words.\n\n## Input\n\n"
        )
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(prompt_content)
        return path

    @patch("src.transformers.llm.transformer.GoogleAIClient")
    def test_llm_transformer_initialization(self, mock_client_class):
        """Test that the LLM transformer can be initialized."""
        # Set up the mock
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        # Initialize the transformer
        transformer = LLMTransformer(
            config={
                "api_key": "mock_api_key",
                "prompt_path": str(self.prompt_path),
                "model_name": "gemini-2.0-flash",
            }
        )

        # Check that client was initialized with expected arguments
        mock_client_class.assert_called_once()

        # Check transformer configuration
        self.assertEqual(transformer.config["model_name"], "gemini-2.0-flash")
        self.assertIsNotNone(transformer.client)

    @patch("src.transformers.llm.client.GoogleAIClient.generate_wordlist")
    def test_transform_with_mock(self, mock_generate):
        """Test the transform method with a mock response."""
        # Set up the mock return value
        mock_generate.return_value = self.mock_response

        # Initialize the transformer with a mock API key
        transformer = LLMTransformer(
            config={
                "api_key": "mock_api_key",
                "prompt_path": str(self.prompt_path),
                "model_name": "gemini-2.0-flash",
            }
        )

        # Transform the sample words
        result = list(transformer.transform(self.sample_words))

        # Check the mock was called with the expected arguments
        mock_generate.assert_called_once()
        args, kwargs = mock_generate.call_args

        # Check that the context contains the input words
        self.assertTrue("words" in kwargs["context"])
        self.assertEqual(kwargs["context"]["words"], self.sample_words)

        # Check the result
        self.assertEqual(len(result), 4)
        self.assertIn("p@ssw0rd", result)

    def test_transform_real_api(self):
        """Test the transform method with the actual API if credentials are available."""
        if not self.api_key:
            self.skipTest("API key not available")

        # Initialize the transformer
        transformer = LLMTransformer(
            config={
                "api_key": self.api_key,
                "prompt_path": str(self.prompt_path),
                "model_name": "gemini-2.0-flash",
            }
        )

        try:
            # Transform the sample words
            result = list(transformer.transform(self.sample_words))

            # Save the result to a file for inspection
            output_file = self.output_dir / "llm_transform_result.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)

            logger.info(f"Saved transformation result to {output_file}")

            # Basic validation of the result
            self.assertTrue(len(result) > 0)
            self.assertTrue(all(isinstance(word, str) for word in result))

        except Exception as e:
            logger.error(f"Error during real API test: {str(e)}")
            self.fail(f"Real API test failed: {str(e)}")

    @patch("src.transformers.llm.client.GoogleAIClient.generate_wordlist")
    def test_full_workflow(self, mock_generate):
        """Test the complete workflow from providing context to saving the response."""
        # Set up the mock
        mock_generate.return_value = self.mock_response

        # Create a test client
        client = GoogleAIClient(
            api_key="mock_api_key",
            model_name="gemini-2.0-flash",
            prompt_path=str(self.prompt_path),
        )

        # 1. Set up the context data
        context = {
            "words": self.sample_words,
            "instructions": "Generate password variations focusing on common substitutions and additions.",
        }

        # 2. Generate wordlist with context
        response = client.generate_wordlist(context=context)

        # 3. Check that the mock was called with the expected arguments
        mock_generate.assert_called_once()
        args, kwargs = mock_generate.call_args
        self.assertEqual(kwargs["context"], context)

        # 4. Save the response to a file
        output_file = self.output_dir / "llm_client_response.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(response, f, indent=2)

        logger.info(f"Saved client response to {output_file}")

        # 5. Basic validation of the response
        self.assertEqual(response, self.mock_response)
        self.assertTrue(all(isinstance(word, str) for word in response))

    @patch("src.transformers.llm.client.GoogleAIClient.generate_wordlist")
    def test_json_output_format(self, mock_generate):
        """Test that the output is always in JSON format."""
        # Set up the mock to return a sample JSON response
        mock_generate.return_value = self.mock_response

        # Create the client directly
        client = GoogleAIClient(
            api_key="mock_api_key",
            model_name="gemini-2.0-flash",
            prompt_path=str(self.prompt_path),
        )

        # Add system instruction to ensure JSON output
        system_instruction = "Always respond with a JSON array of strings. Do not include any explanations or markdown formatting."

        # Generate wordlist with context and explicit JSON instruction
        context = {
            "words": self.sample_words,
            "instructions": "Generate variations. Output must be a plain JSON array only.",
        }

        response = client.generate_wordlist(
            context=context, system_instruction=system_instruction
        )

        # Check that the mock was called with the expected system instruction
        mock_generate.assert_called_once()
        args, kwargs = mock_generate.call_args
        self.assertEqual(kwargs["context"], context)
        self.assertEqual(kwargs["system_instruction"], system_instruction)

        # Save the response to a file
        output_file = self.output_dir / "json_output_response.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(response, f, indent=2)

        logger.info(f"Saved JSON output response to {output_file}")

        # Validate that the response is a list of strings (JSON format)
        self.assertIsInstance(response, list)
        self.assertTrue(all(isinstance(word, str) for word in response))
        self.assertTrue(len(response) > 0)


if __name__ == "__main__":
    unittest.main()
