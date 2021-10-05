import logging
from datetime import datetime
import os



class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""
    #https://github.com/denisb411/btc_watcher/blob/main/utils/logging_utils.py

    grey = "\x1b[38;21m"
    yellow = "\x1b[33;21m"
    light_blue = "\x1b[1;36m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    #format = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
    #format_debug = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s %(name)s"
    format = "[%(asctime)s][%(name)s][%(levelname)s] %(message)s"
    format_debug = "[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)s - %(funcName)s() ][%(name)s] %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format_debug + reset,
        logging.INFO: light_blue + format_debug + reset,
        logging.WARNING: yellow + format_debug + reset,
        logging.ERROR: bold_red + format_debug + reset,
        logging.CRITICAL: bold_red + format_debug + reset
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
    
def create_default_logger(name):
    log_level = os.getenv('LOG_LEVEL', 'DEBUG')
    if log_level == 'DEBUG':
        logging_level = logging.DEBUG
    elif log_level == 'INFO':
        logging_level = logging.INFO
    elif log_level == 'WARNING':
        logging_level = logging.WARNING
    elif log_level == 'ERROR':
        logging_level = logging.ERROR
    elif log_level == 'CRITICAL':
        logging_level = logging.CRITICAL

    logger = logging.getLogger(name)
    logger.setLevel(logging_level)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging_level)

    ch.setFormatter(CustomFormatter())
    
    logger.addHandler(ch)
    
    return logger