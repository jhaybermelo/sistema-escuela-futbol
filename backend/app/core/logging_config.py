import logging
import os
from logging.handlers import TimedRotatingFileHandler

_loggers: dict[str, logging.Logger] = {}


def get_logger(domain: str, log_dir: str = "logs") -> logging.Logger:
    if domain in _loggers:
        return _loggers[domain]

    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger(domain)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

        file_handler = TimedRotatingFileHandler(
            os.path.join(log_dir, f"{domain}.log"), when="midnight", backupCount=30, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    _loggers[domain] = logger
    return logger
