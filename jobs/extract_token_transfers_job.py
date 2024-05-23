from domain.token_transfer import extract_transfer_from_log
from jobs.base_job import BaseJob
from executors.batch_work_executor import BatchWorkExecutor


class ExtractTokenTransfersJob(BaseJob):
    def __init__(
            self,
            logs_iterable,
            batch_size,
            max_workers,
            index_keys):
        self.logs_iterable = logs_iterable

        self.batch_work_executor = BatchWorkExecutor(batch_size, max_workers)
        self.index_keys = index_keys

    def _start(self):
        super()._start()

    def _export(self):
        self.batch_work_executor.execute(self.logs_iterable, self._extract_transfers)

    def _extract_transfers(self, log_dicts):
        for log_dict in log_dicts:
            self._extract_transfer(log_dict)

    def _extract_transfer(self, log_dict):
        token_transfer = extract_transfer_from_log(log_dict)
        if token_transfer is not None:
            if type(token_transfer) is list:
                for t in token_transfer:
                    t['item'] = 'token_transfer'
                    self._export_item(t)
            else:
                token_transfer['item'] = 'token_transfer'
                self._export_item(token_transfer)

    def _end(self):
        self.batch_work_executor.shutdown()
