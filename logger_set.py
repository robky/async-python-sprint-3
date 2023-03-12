import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "my_format": {
            "format": (
                "%(asctime)s.%(msecs)03d [%(levelname)s] "
                "%(name)s: %(message)s"
            ),
            "datefmt": "%d-%m-%Y %H:%M:%S",
        },
    },
    "handlers": {
        "default": {
            "formatter": "my_format",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",  # Default is stderr
        },
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": "INFO",  # Default, to change use setLevel
        }
    },
}


def get_logger(name: str = __name__) -> logging:
    """
    Creates a logging object

    :param name: the name that is displayed in the logs
    :return: Logger
    """
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger(name)
    logger.setLevel("DEBUG")
    return logger
