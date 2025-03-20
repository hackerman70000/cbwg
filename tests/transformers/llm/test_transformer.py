import json
import logging
import os
import unittest
from unittest.mock import MagicMock, patch

from src.transformers.llm.google_api_client import GoogleAIClient
from src.transformers.llm.transformer import LLMTransformer
from src.utils.env import find_project_root, load_environment

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_environment()
project_root = find_project_root()


class TestLLMTransformer(unittest.TestCase):
    """Test suite for the LLM transformer module."""

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
        self.api_key = os.environ.get("GOOGLE_API_KEY")
        self.prompt_path = self._find_or_create_prompt_template()
        self.mock_response = ["p@ssw0rd", "s3curity", "auth123", "password123"]

    def _find_or_create_prompt_template(self):
        prompt_path = project_root / "resources" / "prompts" / "wordlist-generation.md"

        if not prompt_path.exists():
            test_prompt_path = self.output_dir / "test_prompt.md"
            prompt_content = "# Test Prompt\n\nGenerate variations of the input words.\n\n## Input\n\n"

            test_prompt_path.parent.mkdir(exist_ok=True)
            with open(test_prompt_path, "w", encoding="utf-8") as f:
                f.write(prompt_content)

            logger.info(f"Created test prompt at {test_prompt_path}")
            return test_prompt_path

        return prompt_path

    @patch("src.transformers.llm.transformer.GoogleAIClient")
    def test_llm_transformer_initialization(self, mock_client_class):
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        transformer = LLMTransformer(
            config={
                "api_key": "mock_api_key",
                "prompt_path": str(self.prompt_path),
                "model_name": "gemini-2.0-flash",
            }
        )

        mock_client_class.assert_called_once()
        self.assertEqual(transformer.config["model_name"], "gemini-2.0-flash")
        self.assertIsNotNone(transformer.client)

    @patch("src.transformers.llm.transformer.GoogleAIClient.generate_wordlist")
    def test_transform_with_mock(self, mock_generate):
        mock_generate.return_value = self.mock_response

        transformer = LLMTransformer(
            config={
                "api_key": "mock_api_key",
                "prompt_path": str(self.prompt_path),
                "model_name": "gemini-2.0-flash",
            }
        )

        result = list(transformer.transform(self.sample_words))

        mock_generate.assert_called_once()
        args, kwargs = mock_generate.call_args
        self.assertTrue("words" in kwargs["context"])
        self.assertEqual(kwargs["context"]["words"], self.sample_words)
        self.assertEqual(len(result), 4)
        self.assertIn("p@ssw0rd", result)

    @unittest.skipIf(
        not os.environ.get("GOOGLE_API_KEY"),
        "Skipping real API test when API key is not available",
    )
    def test_transform_real_api(self):
        if not self.api_key:
            self.skipTest("API key not available")

        transformer = LLMTransformer(
            config={
                "api_key": self.api_key,
                "prompt_path": str(self.prompt_path),
                "model_name": "gemini-2.0-flash",
            }
        )

        try:
            result = list(transformer.transform(self.sample_words))
            output_file = self.output_dir / "llm_transform_result.json"

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)

            logger.info(f"Saved transformation result to {output_file}")
            self.assertTrue(len(result) > 0)
            self.assertTrue(all(isinstance(word, str) for word in result))

        except Exception as e:
            logger.error(f"Error during real API test: {str(e)}")
            self.fail(f"Real API test failed: {str(e)}")

    @patch("src.transformers.llm.transformer.GoogleAIClient.generate_wordlist")
    def test_validation_of_empty_input(self, mock_generate):
        transformer = LLMTransformer(
            config={
                "api_key": "mock_api_key",
                "prompt_path": str(self.prompt_path),
            }
        )

        result = list(transformer.transform([]))
        self.assertEqual(result, [])

        with self.assertRaises(ValueError):
            list(transformer.transform(["valid", ""]))

        with self.assertRaises(ValueError):
            list(transformer.transform(["valid", 123]))

        mock_generate.assert_not_called()

    @patch.object(GoogleAIClient, "generate_wordlist")
    def test_full_workflow(self, mock_generate):
        mock_generate.return_value = self.mock_response

        client = GoogleAIClient(
            api_key="mock_api_key",
            model_name="gemini-2.0-flash",
            prompt_path=str(self.prompt_path),
        )

        context = {
            "words": self.sample_words,
            "instructions": "Generate password variations focusing on common substitutions and additions.",
        }

        response = client.generate_wordlist(context=context)

        mock_generate.assert_called_once()
        args, kwargs = mock_generate.call_args
        self.assertEqual(kwargs["context"], context)

        output_file = self.output_dir / "llm_client_response.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(response, f, indent=2)

        self.assertEqual(response, self.mock_response)
        self.assertTrue(all(isinstance(word, str) for word in response))

    @patch.object(GoogleAIClient, "generate_wordlist")
    def test_json_output_format(self, mock_generate):
        mock_generate.return_value = self.mock_response

        client = GoogleAIClient(
            api_key="mock_api_key",
            model_name="gemini-2.0-flash",
            prompt_path=str(self.prompt_path),
        )

        system_instruction = "Always respond with a JSON array of strings. Do not include any explanations or markdown formatting."
        context = {
            "words": self.sample_words,
            "instructions": "Generate variations. Output must be a plain JSON array only.",
        }

        response = client.generate_wordlist(
            context=context, system_instruction=system_instruction
        )

        mock_generate.assert_called_once()
        args, kwargs = mock_generate.call_args
        self.assertEqual(kwargs["context"], context)
        self.assertEqual(kwargs["system_instruction"], system_instruction)

        output_file = self.output_dir / "json_output_response.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(response, f, indent=2)

        self.assertIsInstance(response, list)
        self.assertTrue(all(isinstance(word, str) for word in response))
        self.assertTrue(len(response) > 0)


if __name__ == "__main__":
    unittest.main()
