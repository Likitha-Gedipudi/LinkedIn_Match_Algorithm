"""
Centralized logging configuration using Loguru.
Provides structured logging with rotation, retention, and custom formatting.
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger


class Logger:
    """Enterprise logging system with structured output."""
    
    def __init__(
        self,
        log_level: str = "INFO",
        log_format: str = "text",
        log_file: Optional[str] = None,
        rotation: str = "100 MB",
        retention: str = "30 days",
    ):
        """
        Initialize logger configuration.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            log_format: Format type (text or json)
            log_file: Path to log file
            rotation: Log rotation policy
            retention: Log retention policy
        """
        self.log_level = log_level
        self.log_format = log_format
        self.log_file = log_file
        self.rotation = rotation
        self.retention = retention
        
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure logger with custom settings."""
        # Remove default handler
        logger.remove()
        
        # Console handler
        if self.log_format == "json":
            console_format = (
                "{{"
                '"time": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
                '"level": "{level}", '
                '"module": "{module}", '
                '"function": "{function}", '
                '"line": {line}, '
                '"message": "{message}"'
                "}}"
            )
        else:
            console_format = (
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            )
        
        logger.add(
            sys.stderr,
            format=console_format,
            level=self.log_level,
            colorize=True if self.log_format == "text" else False,
        )
        
        # File handler
        if self.log_file:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            if self.log_format == "json":
                file_format = (
                    "{{"
                    '"time": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
                    '"level": "{level}", '
                    '"module": "{module}", '
                    '"function": "{function}", '
                    '"line": {line}, '
                    '"message": "{message}", '
                    '"extra": {extra}'
                    "}}"
                )
            else:
                file_format = console_format
            
            logger.add(
                str(log_path),
                format=file_format,
                level=self.log_level,
                rotation=self.rotation,
                retention=self.retention,
                compression="zip",
                serialize=True if self.log_format == "json" else False,
            )
    
    @staticmethod
    def get_logger():
        """Get the configured logger instance."""
        return logger


# Global logger instance
def get_logger():
    """Get the global logger instance."""
    return logger


# Context manager for operation logging
class LogOperation:
    """Context manager for logging operations with timing."""
    
    def __init__(self, operation_name: str, **context):
        self.operation_name = operation_name
        self.context = context
        self.logger = get_logger()
    
    def __enter__(self):
        self.logger.info(
            f"Starting operation: {self.operation_name}",
            **self.context
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.error(
                f"Operation failed: {self.operation_name}",
                error=str(exc_val),
                **self.context
            )
            return False
        else:
            self.logger.info(
                f"Operation completed: {self.operation_name}",
                **self.context
            )
            return True
