import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables once at module level
load_dotenv()

logger = logging.getLogger(__name__)


class GoogleAIClient:
    """
    Client for communicating with Google's Generative AI models.

    This client handles sending prompts to the model, including context data,
    and processes the responses into structured word lists.
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
            verbose_logging: Whether to log detailed information including full prompts
        """
        self.api_key = self._get_api_key(api_key)
        self.model_name = model_name
        self.timeout = timeout
        self.verbose_logging = verbose_logging
        self.client = genai.Client(api_key=self.api_key)

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
                logger.info(f"Loaded prompt template from {prompt_path}")
        except Exception as e:
            raise IOError(f"Failed to read prompt template: {str(e)}")

    def _prepare_prompt(self, context: Union[str, Dict[str, Any], List[str]]) -> str:
        """
        Prepare the full prompt by combining the static prompt with context.

        Args:
            context: Context data to append to the static prompt

        Returns:
            str: The complete prompt to send to the LLM
        """
        context_str = self._convert_context_to_string(context)
        full_prompt = f"{self.static_prompt}\n\n{context_str}"

        if self.verbose_logging:
            self._log_prompt(full_prompt)

        return full_prompt

    def _convert_context_to_string(
        self, context: Union[str, Dict[str, Any], List[str]]
    ) -> str:
        """
        Convert context data to a string format.

        Args:
            context: Context data in various formats

        Returns:
            str: String representation of the context
        """
        if isinstance(context, dict):
            return json.dumps(context, ensure_ascii=False, indent=2)
        elif isinstance(context, list):
            return "\n".join(context)
        else:
            return str(context)

    def _log_prompt(self, prompt: str) -> None:
        """
        Log the full prompt if verbose logging is enabled.

        Args:
            prompt: The full prompt to log
        """
        logger.info("===== FULL PROMPT TO LLM =====")
        logger.info(prompt)
        logger.info("=============================")

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

        # If we've exhausted retries
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
        prompt = self._prepare_prompt(context)

        # Log context data in compact form
        self._log_context_data(context)

        # Configure the request
        config = self._create_request_config(system_instruction)

        # Define the request operation
        def execute_request():
            logger.debug(f"Sending request to {self.model_name}")
            response = self.client.models.generate_content(
                model=self.model_name, config=config, contents=[prompt]
            )
            return self._process_response(response.text)

        # Execute with retries
        return self._retry_operation(
            operation_name="word list generation",
            operation_func=execute_request,
            max_retries=max_retries,
        )

    def _log_context_data(self, context: Union[str, Dict[str, Any], List[str]]) -> None:
        """
        Log the context data if verbose logging is enabled.

        Args:
            context: The context data to log
        """
        if not self.verbose_logging:
            return

        logger.info("===== CONTEXT DATA =====")
        if isinstance(context, dict):
            logger.info(f"Context (dict): {json.dumps(context, indent=2)}")
        else:
            logger.info(f"Context: {context}")
        logger.info("=======================")

    def _create_request_config(
        self, system_instruction: Optional[str] = None
    ) -> types.GenerateContentConfig:
        """
        Create the request configuration for the LLM.

        Args:
            system_instruction: Optional system instruction to use

        Returns:
            types.GenerateContentConfig: The configured request
        """
        return types.GenerateContentConfig(
            temperature=0.2,  # Lower temperature for more deterministic results
            max_output_tokens=8192,  # Adjust based on expected response size
            system_instruction=system_instruction
            or "Always respond only with a JSON array of strings. No explanations.",
        )

    def _process_response(self, response_text: str) -> List[str]:
        """
        Process the response from the LLM.

        Args:
            response_text: The raw response text

        Returns:
            List[str]: The extracted wordlist

        Raises:
            ValueError: If the response cannot be parsed or doesn't contain words
        """
        try:
            # Extract JSON from the response if it's embedded in markdown
            json_text = self._extract_json_from_response(response_text)

            if self.verbose_logging:
                self._log_response_data(response_text, json_text)

            # Parse the JSON and extract word list
            return self._extract_wordlist_from_json(json_text)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response as JSON: {str(e)}")
            logger.debug(f"Response text: {response_text}")
            raise ValueError(f"Response is not valid JSON: {str(e)}")

    def _extract_json_from_response(self, response_text: str) -> str:
        """
        Extract JSON content from the response text.

        Args:
            response_text: The raw response text

        Returns:
            str: The extracted JSON text
        """
        if "```json" in response_text and "```" in response_text:
            json_text = response_text.split("```json")[1].split("```")[0].strip()
            if self.verbose_logging:
                logger.info("Extracted JSON from markdown code block")
        elif "```" in response_text:
            json_text = response_text.split("```")[1].split("```")[0].strip()
            if self.verbose_logging:
                logger.info("Extracted text from code block")
        else:
            json_text = response_text

        return json_text

    def _log_response_data(self, response_text: str, json_text: str) -> None:
        """
        Log the response data if verbose logging is enabled.

        Args:
            response_text: The raw response text
            json_text: The extracted JSON text
        """
        logger.info("===== RAW RESPONSE =====")
        logger.info(response_text[:500] + ("..." if len(response_text) > 500 else ""))
        logger.info("=======================")
        logger.info("===== EXTRACTED JSON TEXT =====")
        logger.info(json_text[:500] + ("..." if len(json_text) > 500 else ""))
        logger.info("==============================")

    def _extract_wordlist_from_json(self, json_text: str) -> List[str]:
        """
        Extract wordlist from JSON data.

        Args:
            json_text: The JSON text to parse

        Returns:
            List[str]: The extracted wordlist

        Raises:
            ValueError: If the JSON doesn't contain a word list
        """
        # Parse the JSON
        json_data = json.loads(json_text)

        # Extract the word list
        if isinstance(json_data, list):
            if self.verbose_logging:
                logger.info(f"Received list with {len(json_data)} words")
            return json_data
        elif isinstance(json_data, dict) and "words" in json_data:
            if self.verbose_logging:
                logger.info(f"Received dict with {len(json_data['words'])} words")
            return json_data["words"]
        else:
            error_msg = "Response JSON doesn't contain a word list"
            logger.error(error_msg)
            raise ValueError(error_msg)

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
        # Prepare the prompt
        prompt = self._prepare_prompt(context)

        # Configure the request with metadata-specific instruction
        config = types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=8192,
            system_instruction=system_instruction
            or "Always respond only with valid JSON. No explanations.",
        )

        # Define the request operation
        def execute_request():
            logger.debug(f"Sending request to {self.model_name}")
            if self.verbose_logging:
                logger.info("Sending request to generate wordlist with metadata")

            response = self.client.models.generate_content(
                model=self.model_name, config=config, contents=[prompt]
            )
            return self._process_metadata_response(response.text)

        # Execute with retries
        return self._retry_operation(
            operation_name="wordlist with metadata generation",
            operation_func=execute_request,
            max_retries=max_retries,
        )

    def _process_metadata_response(self, response_text: str) -> Dict[str, Any]:
        """
        Process metadata response from the LLM.

        Args:
            response_text: The raw response text

        Returns:
            Dict[str, Any]: Dictionary containing the parsed metadata

        Raises:
            ValueError: If the response cannot be parsed as JSON
        """
        try:
            # Extract JSON from the response
            json_text = self._extract_json_from_response(response_text)

            if self.verbose_logging:
                logger.info("===== RAW METADATA RESPONSE =====")
                logger.info(
                    response_text[:500] + ("..." if len(response_text) > 500 else "")
                )
                logger.info("================================")

            # Parse the JSON
            result = json.loads(json_text)
            if self.verbose_logging:
                logger.info(
                    f"Successfully parsed JSON response with keys: {list(result.keys())}"
                )

            # Validate metadata structure
            if not isinstance(result, dict):
                raise ValueError("Metadata response must be a dictionary")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse metadata response as JSON: {str(e)}")
            logger.debug(f"Response text: {response_text}")
            raise ValueError(f"Metadata response is not valid JSON: {str(e)}")
