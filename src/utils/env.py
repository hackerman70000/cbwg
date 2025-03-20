import logging
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def find_project_root() -> Path:
    """
    Find the project root directory (where .env is located).

    Returns:
        Path: Path to the project root, or current working directory if not found
    """
    current_path = Path.cwd().resolve()

    # Try to find .env in current or parent directories
    while not (current_path / ".env").exists() and current_path != current_path.parent:
        current_path = current_path.parent

    if (current_path / ".env").exists():
        return current_path

    # If no .env found, return current directory as fallback
    return Path.cwd()


def load_environment():
    """Load environment variables from .env file at project root."""
    try:
        project_root = find_project_root()
        env_path = project_root / ".env"

        if env_path.exists():
            logger.info(f"Loading environment variables from {env_path}")
            load_dotenv(env_path)
            return True
        else:
            logger.warning("No .env file found at project root")
            return False
    except Exception as e:
        logger.error(f"Error loading environment variables: {e}")
        return False
