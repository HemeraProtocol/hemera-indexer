import logging
import time
from concurrent import futures

from requests.exceptions import HTTPError
from requests.exceptions import Timeout as RequestsTimeout
from requests.exceptions import TooManyRedirects
from web3._utils.threads import Timeout as Web3Timeout

from hemera.common.utils.exception_control import FastShutdownError, RetriableError
from hemera.indexer.executors.bounded_executor import BoundedExecutor
from hemera.indexer.utils.progress_logger import ProgressLogger

RETRY_EXCEPTIONS = (
    ConnectionError,
    HTTPError,
    RequestsTimeout,
    TooManyRedirects,
    Web3Timeout,
    OSError,
    RetriableError,
)

BATCH_CHANGE_COOLDOWN_PERIOD_SECONDS = 2 * 60


# Executes the given work in batches, reducing the batch size exponentially in case of errors.
class BatchWorkExecutor:
    def __init__(
        self,
        starting_batch_size,
        max_workers,
        job_name="BatchWorkExecutor",
        retry_exceptions=RETRY_EXCEPTIONS,
        max_retries=2,
    ):
        self.batch_size = starting_batch_size
        self.max_batch_size = starting_batch_size
        self.latest_batch_size_change_time = None
        self.max_workers = max_workers
        # Using bounded executor prevents unlimited queue growth
        # and allows monitoring in-progress futures and failing fast in case of errors.
        self.executor = BoundedExecutor(100, self.max_workers)
        self._futures = []
        self.retry_exceptions = retry_exceptions
        self.max_retries = max_retries
        self.logger = logging.getLogger(job_name)
        self.progress_logger = ProgressLogger(name=job_name, logger=self.logger)

    def execute(self, work_iterable, work_handler, collector=None, total_items=None, split_method=None):
        self.progress_logger.start(total_items=total_items)
        submit_batches = (
            dynamic_batch_iterator(work_iterable, lambda: self.batch_size)
            if split_method is None
            else split_method(work_iterable)
        )

        for batch in submit_batches:
            self._check_completed_futures()
            future = self.executor.submit(
                self._fail_safe_execute, work_handler, batch, collector, split_method is not None
            )
            self._futures.append(future)

    def _fail_safe_execute(self, work_handler, batch, collector, custom_splitting):
        try:
            if collector:
                work_handler(batch, collector)
            else:
                work_handler(batch)
            if not custom_splitting:
                self._try_increase_batch_size(len(batch))
        except self.retry_exceptions as e:
            self.logger.exception("An exception occurred while executing work_handler.")
            if not custom_splitting and len(batch) > 1:
                self._try_decrease_batch_size(len(batch))
                self.logger.info("The batch of size {} will be retried one item at a time.".format(len(batch)))
                for sub_batch in dynamic_batch_iterator(batch, lambda: self.batch_size):
                    self._fail_safe_execute(work_handler, sub_batch, collector, custom_splitting)
            else:
                execute_with_retries(
                    work_handler,
                    batch,
                    collector,
                    max_retries=self.max_retries,
                    retry_exceptions=self.retry_exceptions,
                )

        self.progress_logger.track(len(batch))

    # Some acceptable race conditions are possible
    def _try_decrease_batch_size(self, current_batch_size):
        batch_size = self.batch_size
        if batch_size > 1:
            new_batch_size = int(current_batch_size / 2)
            self.logger.info("Reducing batch size to {}.".format(new_batch_size))
            self.batch_size = new_batch_size
            self.latest_batch_size_change_time = time.time()

    def _try_increase_batch_size(self, current_batch_size):
        if current_batch_size * 2 <= self.max_batch_size:
            current_time = time.time()
            latest_batch_size_change_time = self.latest_batch_size_change_time
            seconds_since_last_change = (
                current_time - latest_batch_size_change_time if latest_batch_size_change_time is not None else 0
            )
            if seconds_since_last_change > BATCH_CHANGE_COOLDOWN_PERIOD_SECONDS:
                new_batch_size = current_batch_size * 2
                self.logger.info("Increasing batch size to {}.".format(new_batch_size))
                self.batch_size = new_batch_size
                self.latest_batch_size_change_time = current_time

    def wait(self):
        futures.wait(self._futures)
        self._check_completed_futures()
        if len(self._futures) != 0:
            raise FastShutdownError("Futures failed to complete successfully.")

        self.progress_logger.finish()

    def shutdown(self):
        self.executor.shutdown(wait=10)
        self._check_completed_futures()
        if len(self._futures) != 0:
            raise FastShutdownError("Futures failed to complete successfully.")

        self.progress_logger.finish()

    def _check_completed_futures(self):
        """Fail safe in this case means fail fast. TODO: Add retry logic"""
        for future in self._futures.copy():
            if future.done():
                # Will throw an exception here if the future failed
                future.result()
                self._futures.remove(future)


def execute_with_retries(func, *args, max_retries=5, retry_exceptions=RETRY_EXCEPTIONS, sleep_seconds=5):
    for i in range(max_retries):
        try:
            return func(*args)
        except retry_exceptions:
            logging.exception("An exception occurred while executing execute_with_retries. Retry #{}".format(i))
            if i < max_retries - 1:
                logging.info("The request will be retried after {} seconds. Retry #{}".format(sleep_seconds, i))
                time.sleep(sleep_seconds)
                continue
            else:
                raise


def dynamic_batch_iterator(iterable, batch_size_getter):
    batch = []
    batch_size = batch_size_getter()
    for item in iterable:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
            batch_size = batch_size_getter()
    if len(batch) > 0:
        yield batch
