import logging
import signal
import sys


def logging_basic_config(filename=None):
    format = '%(asctime)s - %(name)s [%(levelname)s] - %(message)s'
    if filename is not None:
        logging.basicConfig(level=logging.INFO, format=format, filename=filename)
    else:
        logging.basicConfig(level=logging.INFO, format=format)

    logging.getLogger('ethereum_dasm.evmdasm').setLevel(logging.ERROR)


def configure_signals():
    def sigterm_handler(_signo, _stack_frame):
        # Raises SystemExit(0):
        sys.exit(0)

    signal.signal(signal.SIGTERM, sigterm_handler)


def configure_logging(filename):
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging_basic_config(filename=filename)
