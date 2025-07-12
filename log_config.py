import logging
import logging.config
from config import config


class ConsoleFormatter(logging.Formatter):
    def format(self, record):

        asctime = self.formatTime(record, self.datefmt)
        message = record.getMessage()
        title = self.title(record.levelname)

        return f"{title}: {self.msg_format(message)} {asctime}\x1b[31m@\x1b[0m{record.filename}:\x1b[35m{record.lineno}\x1b[0m"

    def title(self, levelname: str):
        match levelname:
            case "DEBUG":
                return "[\x1b[32m%s\x1b[0m]" % levelname
            case "INFO":
                return "[\x1b[34m%s\x1b[0m]" % levelname
            case "WARNING":
                return "[\x1b[93m%s\x1b[0m]" % levelname
            case "ERROR":
                return "[\x1b[91m%s\x1b[0m]" % levelname
            case "CRITICAL":
                return "[\x1b[97;101m%s\x1b[0m]" % levelname
            case _:
                return "[\x1b[34m%s\x1b[0m]" % levelname

    def msg_format(self, message: str):
        messages = message.split(" ")
        try:
            status = int(messages[-1])
        except ValueError:
            status = None
        if not status:
            return message
        if status < 300:
            msg_status = "\x1b[92m%d OK\x1b[0m" % status
        else:
            msg_status = "\x1b[91m%d ERROR\x1b[0m" % status
        messages[-1] = msg_status
        return " ".join(messages)


LOGGER_SETTINGS = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console_formatter": {
            "()": ConsoleFormatter,
            "datefmt": "\x1b[36m%H:%M:%S\x1b[0m",
        },
    },
    "handlers": {
        "no_formatter": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            # "formatter": "console_formatter",
        },
        "debug_console": {
            "class": "logging.StreamHandler",  # "rich.logging.RichHandler",  # could use logging.StreamHandler instead
            "level": "DEBUG",
            "formatter": "console_formatter",
        },
        "console": {
            "class": "logging.StreamHandler",  # could use logging.StreamHandler instead
            "level": "INFO",
            "formatter": "console_formatter",
        },
        "logtail": {
            "class": "logtail.LogtailHandler",
            "level": "INFO",
            "source_token": config.LOGTAIL_KEY,
            "host": "https://s1382660.eu-nbg-2.betterstackdata.com",
            "formatter": "console_formatter",
        },
    },
    "loggers": {
        "debug": {
            "level": "DEBUG",
            "handlers": ["debug_console"],
            "propagate": False,  # 防止日志冒泡到根记录器
        },
        "error": {
            "level": "ERROR",
            "handlers": ["logtail"],
            "propagate": False,  # 防止日志冒泡到根记录器
        },
        "uvicorn.access": {"level": "INFO", "handlers": ["logtail"]},
    },
}


if __name__ == "__main__":
    logging.config.dictConfig(LOGGER_SETTINGS)
    log = logging.getLogger("debug")
    log.addHandler(logging.NullHandler())
    # 示例日志
    log.debug("This is a debug message 200")
    log.info("This is an info message")
    log.warning("This is a warning message")
    log.error("This is an error message")
    log.critical("This is a critical message")
