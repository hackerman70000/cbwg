import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from google import genai
from google.genai import types

from src.transformers.llm.client_config import GoogleAIClientConfig
from src.transformers.llm.prompt_handler import PromptHandler
from src.transformers.llm.response_processor import ResponseProcessor

logger = logging.getLogger(__name__)


class GoogleAIClient:
    """
    Client for communicating with Google's Generative AI models.

    This client handles sending prompts to the model and processing responses.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.0-flash",
        prompt_path: Optional[Union[str, Path]] = None,
        timeout: int = 60,
        verbose_logging: bool = False,
    ):
        """
        Initialize the Google AI client.

        Args:
            api_key: Google AI API key. If None, will look for GOOGLE_API_KEY environment variable
            model_name: Name of the model to use
            prompt_path: Path to the static prompt template file (.md)
            timeout: Request timeout in seconds
            verbose_logging: Whether to log detailed information
        """

        self.config = GoogleAIClientConfig(
            api_key=api_key,
            model_name=model_name,
            prompt_path=prompt_path,
            timeout=timeout,
            verbose_logging=verbose_logging,
        )

        self.prompt_handler = PromptHandler(
            static_prompt=self.config.static_prompt, verbose_logging=verbose_logging
        )
        self.response_processor = ResponseProcessor(verbose_logging=verbose_logging)

        self.client = genai.Client(api_key=self.config.api_key)

    def _retry_operation(
        self, operation_name: str, operation_func: callable, max_retries: int
    ) -> Any:
        """
        Retry an operation with multiple attempts.

        Args:
            operation_name: Name of the operation for logging
            operation_func: Function to execute
            max_retries: Maximum number of retry attempts

        Returns:
            Any: The result of the operation

        Raises:
            RuntimeError: If the operation fails after all retries
        """
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                logger.debug(f"Executing {operation_name}")
                return operation_func()
            except Exception as e:
                last_error = e
                retry_count += 1
                logger.warning(
                    f"{operation_name} attempt {retry_count} failed: {str(e)}"
                )

        logger.error(f"Failed to execute {operation_name} after {max_retries} attempts")
        raise RuntimeError(f"Failed to execute {operation_name}: {str(last_error)}")

    def generate_wordlist(
        self,
        context: Union[str, Dict[str, Any], List[str]],
        system_instruction: Optional[str] = None,
        max_retries: int = 3,
    ) -> List[str]:
        """
        Generate a wordlist using the LLM based on provided context.

        Args:
            context: Context data to append to the static prompt
            system_instruction: Optional system instruction to override default
            max_retries: Maximum number of retries on failure

        Returns:
            List[str]: Generated word list

        Raises:
            RuntimeError: If the request fails after all retries
            ValueError: If the response is not valid JSON or doesn't contain words
        """
        prompt = self.prompt_handler.prepare_prompt(context)

        self.prompt_handler.log_context_data(context)

        request_config = self.config.create_request_config(system_instruction)

        def execute_request():
            logger.debug(f"Sending request to {self.config.model_name}")
            response = self.client.models.generate_content(
                model=self.config.model_name,
                config=types.GenerateContentConfig(**request_config),
                contents=[prompt],
            )
            return self.response_processor.process_response(response.text)

        return self._retry_operation(
            operation_name="word list generation",
            operation_func=execute_request,
            max_retries=max_retries,
        )

    def generate_wordlist_with_metadata(
        self,
        context: Union[str, Dict[str, Any], List[str]],
        system_instruction: Optional[str] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Generate a wordlist with additional metadata.

        Args:
            context: Context data to append to the static prompt
            system_instruction: Optional system instruction to override default
            max_retries: Maximum number of retries on failure

        Returns:
            Dict[str, Any]: Dictionary containing words and metadata

        Raises:
            RuntimeError: If the request fails after all retries
            ValueError: If the response is not valid JSON
        """
        prompt = self.prompt_handler.prepare_prompt(context)

        metadata_instruction = (
            system_instruction
            or "Always respond only with valid JSON. No explanations."
        )
        request_config = self.config.create_request_config(metadata_instruction)

        def execute_request():
            logger.debug(f"Sending request to {self.config.model_name}")
            if self.config.verbose_logging:
                logger.info("Sending request to generate wordlist with metadata")

            response = self.client.models.generate_content(
                model=self.config.model_name,
                config=types.GenerateContentConfig(**request_config),
                contents=[prompt],
            )
            return self.response_processor.process_metadata_response(response.text)

        return self._retry_operation(
            operation_name="wordlist with metadata generation",
            operation_func=execute_request,
            max_retries=max_retries,
        )
