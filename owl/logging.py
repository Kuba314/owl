import logging
from typing import ClassVar


def init_logging(level: int = logging.DEBUG) -> None:
    # edited version of https://stackoverflow.com/a/56944256/8844422
    class ColoredLevelnameFormatter(logging.Formatter):
        COLORS: ClassVar = {
            logging.DEBUG: "\x1b[30m",
            logging.INFO: "\x1b[1;34m",
            logging.WARNING: "\x1b[1;33m",
            logging.ERROR: "\x1b[1;31m",
            logging.CRITICAL: "\x1b[37;41m",
        }

        def format(self, record):
            color = self.COLORS.get(record.levelno)
            fmt = f"{{asctime}} {{name:20}} {color}{{levelname:10}}\033[0m {{message}}"
            formatter = logging.Formatter(fmt, style="{")
            return formatter.format(record)

    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(ColoredLevelnameFormatter())
    logger.addHandler(handler)
    logger.setLevel(level)
