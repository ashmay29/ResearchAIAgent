import logging
import sys

_DEF_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

_initialized = False

def get_logger(name: str) -> logging.Logger:
    global _initialized
    if not _initialized:
        logging.basicConfig(level=logging.INFO, format=_DEF_FORMAT, stream=sys.stdout)
        _initialized = True
    return logging.getLogger(name)
