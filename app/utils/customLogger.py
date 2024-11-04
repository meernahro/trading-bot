import logging
from colorama import Fore, Style
import colorama

colorama.init(autoreset=True)

class CustomFormatter(logging.Formatter):
    # Define color mappings for each log level
    LOG_COLORS = {
        logging.DEBUG: Fore.BLUE,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA
    }

    def format(self, record):
        # Choose the color based on the log level
        log_color = self.LOG_COLORS.get(record.levelno, Fore.WHITE)
        log_fmt = f"{log_color}%(asctime)s {Style.RESET_ALL} - {log_color}%(levelname)s{Style.RESET_ALL}: %(message)s"
        formatter = logging.Formatter(log_fmt, "%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

def get_logger(name: str):
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        handler.setFormatter(CustomFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all levels
    return logger
