import logging
import os
import signal
import sys
from fileinput import filename
from logging.handlers import TimedRotatingFileHandler


def logging_basic_config(log_level=logging.INFO, log_file=None):
    format = "%(asctime)s - %(name)s [%(levelname)s] - %(message)s"
    if filename is not None:
        handler = TimedRotatingFileHandler(filename=log_file, when="h", interval=2, backupCount=12)
        logging.basicConfig(level=log_level, format=format, handlers=[handler])
    else:
        logging.basicConfig(level=log_level, format=format)


def configure_signals():
    def sigterm_handler(_signo, _stack_frame):
        # Raises SystemExit(0):
        sys.exit(0)

    signal.signal(signal.SIGTERM, sigterm_handler)


def configure_logging(log_level="INFO", log_file=None):
    if log_file:
        log_dir = os.path.dirname(log_file)

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    level = logging.getLevelName(log_level)
    if level is str:
        raise ValueError("Unknown log level: %r" % log_level)
    logging_basic_config(log_level=level, log_file=log_file)
