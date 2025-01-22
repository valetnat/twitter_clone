import logging
import sys
from pathlib import Path

LOGS_DIR = Path(__file__).parent.parent / "var" / "log" / "twitter_application"


def get_logger(name):
    logger = logging.getLogger(name)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    return logger


dict_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "fileFormatter": {
            "format": "%(asctime)s | %(name)s | %(levelname)s | %(lineno)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "consoleFormatter": {
            "format": "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "uvicornAccessFormatter": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s %(client_addr)s -"%(request_line)s" %(status_code)s',
        },
        "uvicornDefaultFormatter": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(asctime)s - %(message)s",
            "use_colors": None,
        },
    },
    "handlers": {
        "consoleHandler": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "consoleFormatter",
            "stream": sys.stdout,
        },
        "fileDebugHandler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "mode": "a",
            "formatter": "fileFormatter",
            "filename": LOGS_DIR / "app_debug.log",
            "maxBytes": 1024,
            # "backupCount": 1,
        },
        "fileInfoHandler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "mode": "a",
            "formatter": "fileFormatter",
            "filename": LOGS_DIR / "app_info.log",
            "maxBytes": 1024,
            # "backupCount": 1,
        },
        "consoleAccessUvicornHandler": {
            "class": "logging.StreamHandler",
            "formatter": "uvicornAccessFormatter",
            "stream": "ext://sys.stdout",
        },
        "consoleDefaultUvicornHandler": {
            "class": "logging.StreamHandler",
            "formatter": "uvicornDefaultFormatter",
            "stream": "ext://sys.stderr",
        },
    },
    "loggers": {
        # "root": {
        #     "level": "DEBUG",
        #     "handlers": ["consoleHandler"],
        # },
        "app_logger": {
            "level": "DEBUG",
            "handlers": ["consoleHandler", "fileInfoHandler", "fileDebugHandler"],
            "propagate": False,
        },
        "app_logger.services": {
            "level": "DEBUG",
            "handlers": ["consoleHandler", "fileInfoHandler", "fileDebugHandler"],
            "propagate": False,
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["consoleDefaultUvicornHandler", "fileInfoHandler", "fileDebugHandler"],
            "propagate": False,
        },
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["consoleAccessUvicornHandler", "fileInfoHandler", "fileDebugHandler"],
            "propagate": False,
        },
        "uvicorn.error": {"level": "INFO", "propagate": True},
    },
}
