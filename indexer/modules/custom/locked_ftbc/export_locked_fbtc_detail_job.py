import logging

from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.feature_type import FeatureType
from indexer.modules.custom.locked_ftbc import constants
from indexer.modules.custom.locked_ftbc.domain.feature_locked_fbtc_detail import LockedFBTCDetail
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.abi import decode_log

logger = logging.getLogger(__name__)
FEATURE_ID = FeatureType.LOCKED_FBTC_LOGS.value


class ExportLockedFBTCDetailJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [LockedFBTCDetail]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self._batch_size = kwargs["batch_size"]
        self._max_worker = kwargs["max_workers"]

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(topics=[constants.MINT_LOCKED_FBTC_REQUEST_TOPIC0]),
            ]
        )

    def _start(self):
        super()._start()

    def _collect(self, **kwargs):
        transactions = self._data_buff[Transaction.type()]

        self._batch_work_executor.execute(transactions, self._collect_batch, len(transactions))
        self._batch_work_executor.wait()

    def _collect_batch(self, transactions):
        for transaction in transactions:
            from_address = transaction.from_address
            block_number = transaction.block_number
            block_timestamp = transaction.block_timestamp
            if transaction.receipt is None or transaction.receipt.logs is None or len(transaction.receipt.logs) == 0:
                continue
            for log in transaction.receipt.logs:
                topic0 = log.topic0
                # todo need deal the burn request
                if topic0 != constants.MINT_LOCKED_FBTC_REQUEST_TOPIC0:
                    continue
                decode_mint = decode_log(constants.MINT_LOCKED_FBTC_REQUEST_ABI, log)
                mint_entity = LockedFBTCDetail(
                    contract_address=log.address,
                    wallet_address=from_address,
                    minter=decode_mint["minter"],
                    received_amount=decode_mint["receivedAmount"],
                    fee=decode_mint["fee"],
                    log_index=log.log_index,
                    block_number=block_number,
                    block_timestamp=block_timestamp,
                )
                self._collect_item(LockedFBTCDetail.type(), mint_entity)


def _process(self):
    self._data_buff[LockedFBTCDetail.type()].sort(key=lambda x: (x.block_number, x.log_index))
