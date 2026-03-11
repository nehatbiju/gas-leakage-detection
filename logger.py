"""
Logging configuration for the Gas Leak Detection System.
Sets up structured logging with file and console handlers.
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import sys


class LoggerSetup:
    """Configure and manage application logging"""
    
    @staticmethod
    def setup_logger(config) -> logging.Logger:
        """
        Setup application logger with file and console handlers.
        
        Args:
            config: Configuration object containing LOG_DIR and LOG_LEVEL
        
        Returns:
            Configured logger instance
        """
        # Create logs directory if it doesn't exist
        log_dir = getattr(config, 'LOG_DIR', Path('logs'))
        if isinstance(log_dir, str):
            log_dir = Path(log_dir)
        log_dir.mkdir(exist_ok=True, parents=True)
        
        log_level = getattr(config, 'LOG_LEVEL', 'INFO')
        
        # Create logger
        logger = logging.getLogger('gas_leak_detection')
        logger.setLevel(getattr(logging, log_level))
        
        # Avoid duplicate handlers
        if logger.hasHandlers():
            return logger
        
        # Formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler - Rotating file handler to prevent huge log files
        log_file = log_dir / 'app.log'
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, log_level))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        logger.info("Logger initialized successfully")
        
        return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    logger_name = name or 'gas_leak_detection'
    return logging.getLogger(logger_name)
