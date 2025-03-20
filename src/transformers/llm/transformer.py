import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Find the project root directory (where .env is located)
def find_project_root():
    current_path = Path(__file__).resolve()
    while not (current_path / ".env").exists() and current_path != current_path.parent:
        current_path = current_path.parent

    if (current_path / ".env").exists():
        return current_path
    return None


# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    project_root = find_project_root()
    if project_root:
        logger.info(f"Loading .env from: {project_root / '.env'}")
        load_dotenv(project_root / ".env")
        logger.info("Environment variables loaded from .env file")
    else:
        logger.warning("No .env file found in any parent directory")
except ImportError:
    logger.warning(
        "python-dotenv package not installed, environment variables may not be loaded"
    )

# The rest of your transformer module imports and code
try:
    # Import the base Transformer class
    # Assuming it can be found relative to this file location
    try:
        from src.transformers.base import Transformer  # Try standard project structure
    except ImportError:
        # If the standard import path doesn't work, try relative import
        import sys
        from pathlib import Path

        parent_dir = str(Path(__file__).resolve().parent.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from base import Transformer

    # Import the GoogleAIClient
    try:
        from src.transformers.llm.client import (
            GoogleAIClient,  # Try standard project structure
        )
    except ImportError:
        # If the standard import path doesn't work, try relative import
        current_dir = str(Path(__file__).resolve().parent)
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        try:
            from client import GoogleAIClient
        except ImportError:
            logger.error(
                "Could not import GoogleAIClient. Make sure the client module is accessible."
            )

except Exception as e:
    logger.error(f"Error during imports: {str(e)}")


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
        # Check if API key is available
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY not found in environment variables")
        else:
            logger.info(f"GOOGLE_API_KEY found: {api_key[:4]}...{api_key[-4:]}")

        # Initialize the configuration with defaults
        self.config = config or {}
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate the configuration for LLM transformer."""

        # Set default configuration values
        self.config.setdefault("api_key", os.environ.get("GOOGLE_API_KEY"))
        self.config.setdefault("model_name", "gemini-2.0-flash")

        # Look for prompt in standard locations
        prompt_path = None

        # Check for prompt_path in config
        if "prompt_path" in self.config and Path(self.config["prompt_path"]).exists():
            prompt_path = Path(self.config["prompt_path"])
        else:
            # Try to find the prompt in standard locations
            project_root = find_project_root()
            if project_root:
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

        self.config.setdefault("system_instruction", None)
        self.config.setdefault("batch_size", 100)
        self.config.setdefault("max_retries", 3)

        # Initialize the LLM client
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

        # Process words in batches to avoid exceeding token limits
        batch_size = self.config["batch_size"]
        for i in range(0, len(words), batch_size):
            batch = words[i : i + batch_size]

            try:
                # Use the words as context for the LLM
                context = {
                    "words": batch,
                    "instructions": "Generate variations, combinations, and contextually relevant words based on these input words. Focus on creating password-like patterns.",
                }

                # Generate words using the LLM
                generated_words = self.client.generate_wordlist(
                    context=context,
                    system_instruction=self.config["system_instruction"],
                    max_retries=self.config["max_retries"],
                )

                # Return generated words
                for word in generated_words:
                    yield word

            except Exception as e:
                logger.error(f"Failed to transform words using LLM: {str(e)}")
                raise ValueError(f"Failed to transform words using LLM: {str(e)}")

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
