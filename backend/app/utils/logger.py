import logging
import sys
import functools
import time

_DEF_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

_initialized = False

def get_logger(name: str) -> logging.Logger:
    global _initialized
    if not _initialized:
        logging.basicConfig(level=logging.INFO, format=_DEF_FORMAT, stream=sys.stdout)
        _initialized = True
    return logging.getLogger(name)


def track_api_call(call_type: str):
    """Decorator to track and log API calls"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start = time.time()
            logger.info(f"[API_CALL_START] {call_type} - Function: {func.__name__}")
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                logger.info(f"[API_CALL_SUCCESS] {call_type} completed in {duration:.2f}s")
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(f"[API_CALL_FAILED] {call_type} failed after {duration:.2f}s: {e}")
                raise
        return wrapper
    return decorator
