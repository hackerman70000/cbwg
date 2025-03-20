import json
import logging
from typing import Any, Dict, List, Union

logger = logging.getLogger(__name__)


class PromptHandler:
    """Handler for preparing prompts to send to the LLM."""

    def __init__(self, static_prompt: str = "", verbose_logging: bool = False):
        """
        Initialize the prompt handler.

        Args:
            static_prompt: Static prompt template to use
            verbose_logging: Whether to log detailed information
        """
        self.static_prompt = static_prompt
        self.verbose_logging = verbose_logging

    def prepare_prompt(self, context: Union[str, Dict[str, Any], List[str]]) -> str:
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

    def log_context_data(self, context: Union[str, Dict[str, Any], List[str]]) -> None:
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
