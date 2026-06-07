import logging
import sys
from .config import Config

def setup_logging():
    """
    Configures the root logger for the application.
    """
    logging.basicConfig(
        level=Config.LOG_LEVEL,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

def get_logger(name: str):
    """
    Returns a logger instance for a given module name.
    """
    return logging.getLogger(name)

# Initial setup when module is imported
setup_logging()
logger = get_logger("job-hunter-pro")
