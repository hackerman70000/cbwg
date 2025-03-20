import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ResponseProcessor:
    """Processor for LLM responses, handling extraction and validation."""

    def __init__(self, verbose_logging: bool = False):
        """
        Initialize the response processor.

        Args:
            verbose_logging: Whether to log detailed information
        """
        self.verbose_logging = verbose_logging

    def process_response(self, response_text: str) -> List[str]:
        """
        Process the response from the LLM to extract a wordlist.

        Args:
            response_text: The raw response text

        Returns:
            List[str]: The extracted wordlist

        Raises:
            ValueError: If the response cannot be parsed or doesn't contain words
        """
        try:
            json_text = self._extract_json_from_response(response_text)

            if self.verbose_logging:
                self._log_response_data(response_text, json_text)

            return self._extract_wordlist_from_json(json_text)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response as JSON: {str(e)}")
            logger.debug(f"Response text: {response_text}")
            raise ValueError(f"Response is not valid JSON: {str(e)}")

    def process_metadata_response(self, response_text: str) -> Dict[str, Any]:
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
            json_text = self._extract_json_from_response(response_text)

            if self.verbose_logging:
                logger.info("===== RAW METADATA RESPONSE =====")
                logger.info(
                    response_text[:500] + ("..." if len(response_text) > 500 else "")
                )
                logger.info("================================")

            result = json.loads(json_text)

            if not isinstance(result, dict):
                raise ValueError("Metadata response must be a dictionary")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse metadata response as JSON: {str(e)}")
            logger.debug(f"Response text: {response_text}")
            raise ValueError(f"Metadata response is not valid JSON: {str(e)}")

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
        json_data = json.loads(json_text)

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
