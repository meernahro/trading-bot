import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from ..config import LOG_LEVEL

# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

def get_logger(name: str) -> logging.Logger:
    """
    Creates or returns a logger with the specified name and consistent formatting
    
    Args:
        name (str): Name of the logger
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure the logger if it hasn't been configured before
    if not logger.handlers:
        logger.setLevel(getattr(logging, LOG_LEVEL.upper()))
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create and configure file handler
        file_handler = RotatingFileHandler(
            f"logs/{name}.log",
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        
        # Create and configure console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
    return logger
