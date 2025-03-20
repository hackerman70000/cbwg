import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from google import genai
from google.genai import types

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
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key must be provided or set as GOOGLE_API_KEY environment variable"
            )

        self.model_name = model_name
        self.timeout = timeout
        self.verbose_logging = verbose_logging
        self.client = genai.Client(api_key=self.api_key)

        self.static_prompt = ""
        if prompt_path:
            self.load_prompt_template(prompt_path)

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
        if isinstance(context, dict):
            context_str = json.dumps(context, ensure_ascii=False, indent=2)
        elif isinstance(context, list):
            context_str = "\n".join(context)
        else:
            context_str = str(context)

        full_prompt = f"{self.static_prompt}\n\n{context_str}"

        if self.verbose_logging:
            logger.info("===== FULL PROMPT TO LLM =====")
            logger.info(full_prompt)
            logger.info("=============================")

        return full_prompt

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

        # Log the context being sent (compact form)
        if self.verbose_logging:
            logger.info("===== CONTEXT DATA =====")
            if isinstance(context, dict):
                logger.info(f"Context (dict): {json.dumps(context, indent=2)}")
            else:
                logger.info(f"Context: {context}")
            logger.info("=======================")

        # Configure the request
        config = types.GenerateContentConfig(
            temperature=0.2,  # Lower temperature for more deterministic results
            max_output_tokens=8192,  # Adjust based on expected response size
            system_instruction=system_instruction
            or "Always respond only with a JSON array of strings. No explanations.",
        )

        # Execute with retries
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                logger.debug(f"Sending request to {self.model_name}")
                response = self.client.models.generate_content(
                    model=self.model_name, config=config, contents=[prompt]
                )

                # Process the response
                response_text = response.text
                try:
                    # Extract JSON from the response if it's embedded in markdown
                    if "```json" in response_text and "```" in response_text:
                        json_text = (
                            response_text.split("```json")[1].split("```")[0].strip()
                        )
                        if self.verbose_logging:
                            logger.info("Extracted JSON from markdown code block")
                    elif "```" in response_text:
                        json_text = (
                            response_text.split("```")[1].split("```")[0].strip()
                        )
                        if self.verbose_logging:
                            logger.info("Extracted text from code block")
                    else:
                        json_text = response_text

                    if self.verbose_logging:
                        logger.info("===== RAW RESPONSE =====")
                        logger.info(
                            response_text[:500]
                            + ("..." if len(response_text) > 500 else "")
                        )
                        logger.info("=======================")
                        logger.info("===== EXTRACTED JSON TEXT =====")
                        logger.info(
                            json_text[:500] + ("..." if len(json_text) > 500 else "")
                        )
                        logger.info("==============================")

                    # Parse the JSON
                    json_data = json.loads(json_text)

                    # Extract the word list
                    if isinstance(json_data, list):
                        if self.verbose_logging:
                            logger.info(f"Received list with {len(json_data)} words")
                        return json_data
                    elif isinstance(json_data, dict) and "words" in json_data:
                        if self.verbose_logging:
                            logger.info(
                                f"Received dict with {len(json_data['words'])} words"
                            )
                        return json_data["words"]
                    else:
                        error_msg = "Response JSON doesn't contain a word list"
                        logger.error(error_msg)
                        raise ValueError(error_msg)

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse response as JSON: {str(e)}")
                    logger.debug(f"Response text: {response_text}")
                    raise ValueError(f"Response is not valid JSON: {str(e)}")

            except Exception as e:
                last_error = e
                retry_count += 1
                logger.warning(f"Request attempt {retry_count} failed: {str(e)}")

        # If we've exhausted retries
        logger.error(f"Failed to generate word list after {max_retries} attempts")
        raise RuntimeError(f"Failed to generate word list: {str(last_error)}")

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

        # Configure the request
        config = types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=8192,
            system_instruction=system_instruction
            or "Always respond only with valid JSON. No explanations.",
        )

        # Execute with retries
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                logger.debug(f"Sending request to {self.model_name}")
                if self.verbose_logging:
                    logger.info("Sending request to generate wordlist with metadata")

                response = self.client.models.generate_content(
                    model=self.model_name, config=config, contents=[prompt]
                )

                # Process the response
                response_text = response.text
                try:
                    # Extract JSON from the response if it's embedded in markdown
                    if "```json" in response_text and "```" in response_text:
                        json_text = (
                            response_text.split("```json")[1].split("```")[0].strip()
                        )
                    elif "```" in response_text:
                        json_text = (
                            response_text.split("```")[1].split("```")[0].strip()
                        )
                    else:
                        json_text = response_text

                    if self.verbose_logging:
                        logger.info("===== RAW METADATA RESPONSE =====")
                        logger.info(
                            response_text[:500]
                            + ("..." if len(response_text) > 500 else "")
                        )
                        logger.info("================================")

                    # Parse the JSON
                    result = json.loads(json_text)
                    if self.verbose_logging:
                        logger.info(
                            f"Successfully parsed JSON response with keys: {list(result.keys())}"
                        )
                    return result

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse response as JSON: {str(e)}")
                    logger.debug(f"Response text: {response_text}")
                    raise ValueError(f"Response is not valid JSON: {str(e)}")

            except Exception as e:
                last_error = e
                retry_count += 1
                logger.warning(f"Request attempt {retry_count} failed: {str(e)}")

        # If we've exhausted retries
        logger.error(f"Failed to generate word list after {max_retries} attempts")
        raise RuntimeError(f"Failed to generate word list: {str(last_error)}")
