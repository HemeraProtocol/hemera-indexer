import logging
import time

from requests.exceptions import Timeout as RequestsTimeout, HTTPError, TooManyRedirects
from web3._utils.threads import Timeout as Web3Timeout

from executors.bounded_executor import BoundedExecutor
from utils.progress_logger import ProgressLogger
from utils.utils import dynamic_batch_iterator

RETRY_EXCEPTIONS = (ConnectionError, HTTPError, RequestsTimeout, TooManyRedirects, Web3Timeout, OSError)

BATCH_CHANGE_COOLDOWN_PERIOD_SECONDS = 2 * 60


# Executes the given work in batches, reducing the batch size exponentially in case of errors.
class BatchWorkExecutor:
    def __init__(self, starting_batch_size, max_workers, retry_exceptions=RETRY_EXCEPTIONS, max_retries=5):
        self.batch_size = starting_batch_size
        self.max_batch_size = starting_batch_size
        self.latest_batch_size_change_time = None
        self.max_workers = max_workers
        # Using bounded executor prevents unlimited queue growth
        # and allows monitoring in-progress futures and failing fast in case of errors.
        self.executor = BoundedExecutor(1, self.max_workers)
        self._futures = []
        self.retry_exceptions = retry_exceptions
        self.max_retries = max_retries
        self.progress_logger = ProgressLogger()
        self.logger = logging.getLogger('BatchWorkExecutor')

    def execute(self, work_iterable, work_handler, total_items=None):
        self.progress_logger.start(total_items=total_items)
        for batch in dynamic_batch_iterator(work_iterable, lambda: self.batch_size):
            self._check_completed_futures()
            future = self.executor.submit(self._fail_safe_execute, work_handler, batch)
            self._futures.append(future)

    def _fail_safe_execute(self, work_handler, batch):
        try:
            work_handler(batch)
            self._try_increase_batch_size(len(batch))
        except self.retry_exceptions:
            self.logger.exception('An exception occurred while executing work_handler.')
            self._try_decrease_batch_size(len(batch))
            self.logger.info('The batch of size {} will be retried one item at a time.'.format(len(batch)))
            for item in batch:
                execute_with_retries(work_handler, [item],
                                     max_retries=self.max_retries, retry_exceptions=self.retry_exceptions)

        self.progress_logger.track(len(batch))

    # Some acceptable race conditions are possible
    def _try_decrease_batch_size(self, current_batch_size):
        batch_size = self.batch_size
        if batch_size == current_batch_size and batch_size > 1:
            new_batch_size = int(current_batch_size / 2)
            self.logger.info('Reducing batch size to {}.'.format(new_batch_size))
            self.batch_size = new_batch_size
            self.latest_batch_size_change_time = time.time()

    def _try_increase_batch_size(self, current_batch_size):
        if current_batch_size * 2 <= self.max_batch_size:
            current_time = time.time()
            latest_batch_size_change_time = self.latest_batch_size_change_time
            seconds_since_last_change = current_time - latest_batch_size_change_time \
                if latest_batch_size_change_time is not None else 0
            if seconds_since_last_change > BATCH_CHANGE_COOLDOWN_PERIOD_SECONDS:
                new_batch_size = current_batch_size * 2
                self.logger.info('Increasing batch size to {}.'.format(new_batch_size))
                self.batch_size = new_batch_size
                self.latest_batch_size_change_time = current_time

    def shutdown(self):
        self.executor.shutdown(wait=True)
        self._check_completed_futures()
        assert len(self._futures) == 0

        self.progress_logger.finish()

    def _check_completed_futures(self):
        """Fail safe in this case means fail fast. TODO: Add retry logic"""
        for future in self._futures.copy():
            if future.done():
                # Will throw an exception here if the future failed
                future.result()
                self._futures.remove(future)


def execute_with_retries(func, *args, max_retries=5, retry_exceptions=RETRY_EXCEPTIONS, sleep_seconds=1):
    for i in range(max_retries):
        try:
            return func(*args)
        except retry_exceptions:
            logging.exception('An exception occurred while executing execute_with_retries. Retry #{}'.format(i))
            if i < max_retries - 1:
                logging.info('The request will be retried after {} seconds. Retry #{}'.format(sleep_seconds, i))
                time.sleep(sleep_seconds)
                continue
            else:
                raise
