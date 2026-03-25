import os
import sys
import logging

ENABLE_TEST_LOGS = False
IS_TEST = "test" in sys.argv
IS_DEV = os.getenv("ENVIRONMENT") == "dev"

DEFAULT_HANDLER = "console" if (not IS_TEST or ENABLE_TEST_LOGS) else "null"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(levelname)s | %(name)s | %(message)s",
        },
        "verbose": {
            "format": "%(levelname)s | %(asctime)s | %(name)s | %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose" if IS_DEV else "simple",
        },
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": [DEFAULT_HANDLER],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": [DEFAULT_HANDLER],
            "level": "INFO" if IS_DEV else "WARNING",
            "propagate": False,
        },
        "core": {
            "handlers": [DEFAULT_HANDLER],
            "level": "DEBUG" if IS_DEV else "INFO",
            "propagate": False,
        },
        "user": {
            "handlers": [DEFAULT_HANDLER],
            "level": "DEBUG" if IS_DEV else "INFO",
            "propagate": False,
        },
        "workout": {
            "handlers": [DEFAULT_HANDLER],
            "level": "DEBUG" if IS_DEV else "INFO",
            "propagate": False,
        },
    },
}

# ---------------------------------------------------------------------
# HARD DISABLE LOGGING DURING TESTS IF ENABLE_TEST_LOGS = False
# ---------------------------------------------------------------------
if IS_TEST and not ENABLE_TEST_LOGS:
    logging.disable(logging.CRITICAL)
