import logging
import os
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from src.transformers.base import Transformer
from src.utils.env import find_project_root

from trans_engine import run as hashcat_run

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class RuleTransformer(Transformer):
    """
    A transformer that applies hashcat rules to generate new words.

    This transformer takes input words and applies a set of rules to generate
    variations, combinations, and contextually relevant new words.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a rule-based transformer.

        Args:
            config: Optional configuration dictionary with the following options:
                - rules_path: Path to the rules file (default: from environment)
                - batch_size: Maximum words to process in one batch (default: 10000)
                - verbose_logging: Whether to enable verbose logging (default: False)
                - rules: List of additional rules to apply (default: None)
        """
        super().__init__(config)
    
    def _validate_config(self) -> None:
        """
        Validate the configuration for rule transformer.
        
        Raises:
            ValueError: If no rules or rules path is provided
        """

        self.config.setdefault("rules_path", os.environ.get("HASHCAT_RULES_PATH") or self._get_default_rule_path())
        self.config.setdefault("verbose_logging", False)
        self.config.setdefault("batch_size", 10000)
        self.config.setdefault("rules", [])

        if not self.config["rules_path"] and not self.config["rules"]:
            logger.warning("No rules path provided in config or environment")
            raise ValueError(
                "Rules path is required. Set it in config or HASHCAT_RULES_PATH environment variable"
            )

        self._setup_rules()
    
    def _get_default_rule_path(self) -> Optional[Path]:
        """
        Get the default path for hashcat rules.

        Returns:
            Optional[Path]: Default path for hashcat rules or None if not found
        """
        project_root = find_project_root()
        if project_root:
            return project_root / "resources" / "rules"
        return None

    def _setup_rules(self) -> None:
        """
        Load rules from the specified path and apply additional rules if provided.
        """
        rules_path = Path(self.config["rules_path"])
        if not rules_path.exists():
            logger.warning(f"Rules path does not exist: {rules_path}")
            raise FileNotFoundError(f"Rules path does not exist: {rules_path}")

        self.rules = []
        for rule_file in rules_path.glob("*.rule"):
            with open(rule_file, "r") as f:
                self.rules.extend(f.readlines())

        if self.config["rules"]:
            self.rules.extend(self.config["rules"])
    
    def transform(self, words: List[str]) -> Iterator[str]:
        """
        Apply the rules to the input words and yield transformed words.

        Args:
            words: List of input words to transform

        Returns:
            Iterator[str]: Generator yielding transformed words

        Raises:
            ValueError: If any word is not a string
        """
        if not words:
            return
        
        self._validate_input_words(words)
        
        batch_size = self.config["batch_size"]
        for i in range(0, len(words), batch_size):
            batch = words[i : i + batch_size]
            yield from hashcat_run(
                rules=self.rules,
                words=batch,
            )
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

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the transformer.
        Returns:
            Dict[str, Any]: Dictionary with transformer metadata
        """
        return {
            "transformer_type": "rule",
            "rules_path": self.config["rules_path"],
            "batch_size": self.config["batch_size"],
        }