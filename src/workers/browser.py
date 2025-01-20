from typing import final

from ..utils.logger import get_logger

logger = get_logger(__name__)


@final
class Browser:
    """Playwright based Browser"""

    def __init__(self, name: str):
        self.name = name
        logger.info(f"Browser {self.name} initialized")
