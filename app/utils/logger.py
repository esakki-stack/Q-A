"""Centralized logging utilities for the application.

Provides a `setup_logger` helper and a module-level `logger` configured
with a sensible default so other modules can import and use it.
"""
import logging
import sys
from typing import Optional


def setup_logger(name: str = "news_qa", level: int = logging.INFO) -> logging.Logger:
	"""Create and configure a logger instance.

	Args:
		name: Logger name.
		level: Logging level (e.g., logging.INFO).

	Returns:
		Configured logging.Logger instance.
	"""
	logger = logging.getLogger(name)
	logger.setLevel(level)

	# Avoid adding multiple handlers if logger already configured
	if not logger.handlers:
		handler = logging.StreamHandler(sys.stdout)
		formatter = logging.Formatter(
			"%(asctime)s - %(levelname)s - %(name)s - %(message)s",
			datefmt="%Y-%m-%d %H:%M:%S",
		)
		handler.setFormatter(formatter)
		logger.addHandler(handler)
		logger.propagate = False

	return logger


# Module-level default logger
logger: logging.Logger = setup_logger()


__all__ = ["setup_logger", "logger"]
