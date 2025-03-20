import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)


class GoogleAIClientConfig:
    """Configuration handler for Google AI Client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.0-flash",
        prompt_path: Optional[Union[str, Path]] = None,
        timeout: int = 60,
        verbose_logging: bool = False,
        temperature: float = 0.2,
        max_output_tokens: int = 8192,
    ):
        """
        Initialize configuration for Google AI Client.

        Args:
            api_key: Google AI API key. If None, will look for GOOGLE_API_KEY environment variable
            model_name: Name of the model to use
            prompt_path: Path to the static prompt template file (.md)
            timeout: Request timeout in seconds
            verbose_logging: Whether to log detailed information
            temperature: Temperature setting for generation (0-1)
            max_output_tokens: Maximum number of tokens in the output
        """
        self.api_key = self._get_api_key(api_key)
        self.model_name = model_name
        self.prompt_path = prompt_path
        self.timeout = timeout
        self.verbose_logging = verbose_logging
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

        self.static_prompt = ""
        if prompt_path:
            self.load_prompt_template(prompt_path)

    def _get_api_key(self, api_key: Optional[str]) -> str:
        """
        Get the API key from the provided parameter or environment variable.

        Args:
            api_key: The API key provided to the constructor

        Returns:
            str: The API key to use

        Raises:
            ValueError: If no API key is available
        """
        key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise ValueError(
                "API key must be provided or set as GOOGLE_API_KEY environment variable"
            )
        return key

    def load_prompt_template(self, prompt_path: Union[str, Path]) -> None:
        """
        Load a prompt template from a markdown file.

        Args:
            prompt_path: Path to the prompt template file

        Raises:
            FileNotFoundError: If the prompt file doesn't exist
            IOError: If there's an error reading the file
        """
        path = Path(prompt_path)
        if not path.exists():
            raise FileNotFoundError(f"Prompt template not found at {prompt_path}")

        try:
            with open(path, "r", encoding="utf-8") as file:
                self.static_prompt = file.read()
        except Exception as e:
            raise IOError(f"Failed to read prompt template: {str(e)}")

    def create_request_config(
        self, system_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create the request configuration for the LLM.

        Args:
            system_instruction: Optional system instruction to use

        Returns:
            Dict[str, Any]: Configuration dictionary for the request
        """
        default_instruction = (
            "Always respond only with a JSON array of strings. No explanations."
        )

        return {
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "system_instruction": system_instruction or default_instruction,
        }
