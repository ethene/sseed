"""Logging configuration for sseed application.

Provides structured logging configuration with separate log files for different
components as specified in user rules.
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Any


def setup_logging(log_level: str = "INFO", log_dir: str = "logs") -> None:
    """Set up structured logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_dir: Directory to store log files.
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "format": "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": (
                    "%(asctime)s | %(name)s | %(levelname)s | "
                    "%(funcName)s:%(lineno)d | %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "structured",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "detailed",
                "filename": log_path / "sseed.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
            "security": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "WARNING",
                "formatter": "detailed",
                "filename": log_path / "security.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "encoding": "utf8",
            },
        },
        "loggers": {
            "sseed": {
                "level": log_level,
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "sseed.security": {
                "level": "WARNING",
                "handlers": ["security"],
                "propagate": False,
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
    }

    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name.

    Args:
        name: Logger name, typically __name__.

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)


def log_security_event(message: str, extra_data: dict[str, Any] | None = None) -> None:
    """Log security-related events to dedicated security log.

    Args:
        message: Security event message.
        extra_data: Additional context data.
    """
    security_logger = logging.getLogger("sseed.security")
    if extra_data:
        security_logger.warning("%s | Extra: %s", message, extra_data)
    else:
        security_logger.warning(message)
