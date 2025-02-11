import logging
import time
from typing import final, override


@final
class ElapsedTimeFormatter(logging.Formatter):
    """Custom formatter to display elapsed time in hh:mm:ss format."""

    def __init__(
        self,
        start_time: float,
        fmt: str = "%(elapsed_time)s - %(name)s - %(levelname)s - %(message)s",
    ):
        super().__init__(fmt)
        self.start_time = start_time

    @override
    def format(self, record: logging.LogRecord) -> str:
        elapsed_seconds = int(time.time() - self.start_time)
        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        record.elapsed_time = f"{hours:02}:{minutes:02}:{seconds:02}"
        return super().format(record)


def get_logger(name: str, start_time: float) -> logging.Logger:
    """Configure and return a logger instance with elapsed time formatting."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = ElapsedTimeFormatter(start_time)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
