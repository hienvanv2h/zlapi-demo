import os
import logging
import colorlog
from logging.handlers import TimedRotatingFileHandler

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def setup_logger(name, log_file=None, level=logging.INFO):
    """
    Setup a logger.

    Args:
        name (str): The name of the logger.
        log_file (str): The path to the log file.
        level (int): The logging level.

    Returns:
        logging.Logger: The configured logger.
    """
    # Create the logger
    logger = logging.getLogger(name)
    # Check if the logger has already been configured
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    log_format = "[%(name)s] %(asctime)s - %(levelname)s - %(message)s"

    console_formatter = colorlog.ColoredFormatter(
        f'%(log_color)s{log_format}',
        log_colors={
            "DEBUG": "cyan",
            "INFO": "blue",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Create a file handler if a log file is provided
    if log_file:
        log_dir = os.path.join(ROOT_DIR, "logs")
        os.makedirs(log_dir, exist_ok=True)

        log_file_path = os.path.join(log_dir, log_file)
        file_handler = TimedRotatingFileHandler(log_file_path, when="midnight", backupCount=7, encoding="utf-8")
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(log_format)
        file_handler.setFormatter(file_formatter)
        file_handler.suffix = "%Y%m%d"
        logger.addHandler(file_handler)

    return logger

def get_logger(name):
    """
    Get a logger by name. If it doesn't exist, create one without file handler.
    
    Returns:
        logging.Logger: The logger instance.
    """
    return logging.getLogger(name) if logging.getLogger(name).handlers else setup_logger(name=name)