import logging
import os
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from src.transformers.base import Transformer
from src.transformers.llm.client import GoogleAIClient

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LLMTransformer(Transformer):
    """
    A transformer that uses Large Language Models to generate new words.

    This transformer takes input words and uses an LLM to generate
    variations, combinations, and contextually relevant new words.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize an LLM-based transformer.

        Args:
            config: Optional configuration dictionary with the following options:
                - api_key: Google AI API key (default: from environment)
                - model_name: Model to use (default: "gemini-2.0-flash")
                - prompt_path: Path to the static prompt template
                - system_instruction: Optional system instruction (default: None)
                - batch_size: Maximum words to process in one batch (default: 100)
                - max_retries: Maximum number of retries on failure (default: 3)
        """
        self.client = None
        super().__init__(config)

    def _validate_config(self) -> None:
        """Validate the configuration for LLM transformer."""
        # Set default configuration values
        self.config.setdefault("api_key", os.environ.get("GOOGLE_API_KEY"))
        self.config.setdefault("model_name", "gemini-2.0-flash")
        self.config.setdefault("system_instruction", None)
        self.config.setdefault("batch_size", 100)
        self.config.setdefault("max_retries", 3)

        # Check for API key
        if not self.config["api_key"]:
            logger.warning("No API key provided in config or environment")
            raise ValueError(
                "API key is required. Set it in config or GOOGLE_API_KEY environment variable"
            )

        # Find prompt path
        self._setup_prompt_path()

        # Initialize the LLM client
        self._initialize_client()

    def _setup_prompt_path(self) -> None:
        """Set up the prompt path from config or look in standard locations."""
        # Look for prompt in standard locations
        prompt_path = None

        # Check for prompt_path in config
        if "prompt_path" in self.config and Path(self.config["prompt_path"]).exists():
            prompt_path = Path(self.config["prompt_path"])
        else:
            # Try to find the prompt in standard locations - project root is where .env is located
            project_root = Path.cwd()
            while (
                not (project_root / ".env").exists()
                and project_root != project_root.parent
            ):
                project_root = project_root.parent

            if (project_root / ".env").exists():
                # Try resources/prompts directory
                resources_path = (
                    project_root / "resources" / "prompts" / "wordlist-generation.md"
                )
                if resources_path.exists():
                    prompt_path = resources_path

        if prompt_path:
            logger.info(f"Using prompt template: {prompt_path}")
            self.config["prompt_path"] = str(prompt_path)
        else:
            logger.warning("No prompt template found, will use default prompt")

    def _initialize_client(self) -> None:
        """Initialize the Google AI client."""
        try:
            self.client = GoogleAIClient(
                api_key=self.config["api_key"],
                model_name=self.config["model_name"],
                prompt_path=self.config.get("prompt_path"),
            )
            logger.info("GoogleAIClient initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {str(e)}")
            raise ValueError(f"Failed to initialize LLM client: {str(e)}")

    def transform(self, words: List[str]) -> Iterator[str]:
        """
        Transform input words using LLM to generate new candidate words.

        Args:
            words: List of input words to transform

        Returns:
            Iterator[str]: An iterator over generated words

        Raises:
            ValueError: If the transformation cannot be performed
        """
        if not words:
            return

        # Validate input words
        self._validate_input_words(words)

        # Process words in batches to avoid exceeding token limits
        batch_size = self.config["batch_size"]
        for i in range(0, len(words), batch_size):
            batch = words[i : i + batch_size]
            yield from self._process_batch(batch)

    def _validate_input_words(self, words: List[str]) -> None:
        """
        Validate the input words to ensure they are strings and not empty.

        Args:
            words: List of input words to validate

        Raises:
            ValueError: If any word is not a string or is empty
        """
        if not all(isinstance(word, str) for word in words):
            raise ValueError("All input words must be strings")

        if any(not word.strip() for word in words):
            raise ValueError("Input words cannot be empty strings")

    def _process_batch(self, batch: List[str]) -> Iterator[str]:
        """
        Process a batch of words with the LLM client.

        Args:
            batch: A batch of words to process

        Returns:
            Iterator[str]: An iterator over generated words

        Raises:
            ValueError: If the batch processing fails
        """
        try:
            # Use the words as context for the LLM
            context = self._create_context(batch)

            # Generate words using the LLM
            generated_words = self.client.generate_wordlist(
                context=context,
                system_instruction=self.config["system_instruction"],
                max_retries=self.config["max_retries"],
            )

            # Validate generated words
            validated_words = self._validate_generated_words(generated_words)

            # Return generated words
            for word in validated_words:
                yield word

        except Exception as e:
            logger.error(f"Failed to transform words using LLM: {str(e)}")
            raise ValueError(f"Failed to transform words using LLM: {str(e)}")

    def _create_context(self, batch: List[str]) -> Dict[str, Any]:
        """
        Create context dictionary for the LLM request.

        Args:
            batch: A batch of words to include in the context

        Returns:
            Dict[str, Any]: Context dictionary for the LLM
        """
        return {
            "words": batch,
            "instructions": "Generate variations, combinations, and contextually relevant words based on these input words. Focus on creating password-like patterns.",
        }

    def _validate_generated_words(self, words: List[str]) -> List[str]:
        """
        Validate generated words from the LLM.

        Args:
            words: List of words generated by the LLM

        Returns:
            List[str]: Validated words

        Raises:
            ValueError: If the generated words are invalid
        """
        if not isinstance(words, list):
            raise ValueError(f"Expected a list of words but got {type(words)}")

        # Filter out any non-string values
        string_words = [word for word in words if isinstance(word, str)]

        # Filter out empty strings
        valid_words = [word for word in string_words if word.strip()]

        if len(valid_words) < len(words):
            logger.warning(
                f"Filtered out {len(words) - len(valid_words)} invalid words"
            )

        return valid_words

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the LLM transformer.

        Returns:
            Dict[str, Any]: Dictionary with transformer metadata
        """
        return {
            "transformer_type": "llm",
            "model_name": self.config["model_name"],
            "prompt_path": self.config.get("prompt_path", "default_prompt"),
            "batch_size": self.config["batch_size"],
        }
