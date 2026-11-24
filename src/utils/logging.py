"""Structured logging configuration for WATERPRINT."""

import os
import sys
import logging
from typing import Optional

def setup_logger(
    name: str = "waterprint",
    log_file: Optional[str] = "reports/waterprint.log",
    level: int = logging.INFO
) -> logging.Logger:
    """Configures a standardized structured logger with both console and file handlers.
    
    Args:
        name: Name of the logger instance.
        log_file: Relative or absolute path to the log file.
        level: Logging level (e.g. logging.INFO, logging.DEBUG).
        
    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers if already configured
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | [%(name)s:%(filename)s:%(lineno)d] | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger

logger = setup_logger()
