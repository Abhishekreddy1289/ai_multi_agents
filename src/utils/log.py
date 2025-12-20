# log.py
import sys
from loguru import logger


class AppLogger:
    """
    Centralized application logger using Loguru.
    """

    @classmethod
    def setup(
        cls,
        log_file: str = "logs/app.log",
        level: str = "INFO",
    ):
        """Initialize logger configuration"""

        # Remove default Loguru handler
        logger.remove()

        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

        # Console logger
        logger.add(
            sys.stdout,
            format=log_format,
            level=level,
            colorize=True,
            enqueue=True,
            backtrace=True,
            diagnose=True,
            catch=True,
        )

        # File logger (rotating)
        logger.add(
            log_file,
            format=log_format,
            level=level,
            rotation="10 MB",
            retention="14 days",
            compression="zip",
            enqueue=True,
            backtrace=True,
            diagnose=True,
            catch=True,
        )

        return logger

    # --- Convenience wrappers ---
    @staticmethod
    def info(message: str):
        logger.info(message)

    @staticmethod
    def success(message: str):
        logger.success(message)

    @staticmethod
    def warning(message: str):
        logger.warning(message)

    @staticmethod
    def error(message: str):
        logger.error(message)

    @staticmethod
    def exception(message: str):
        logger.exception(message)
