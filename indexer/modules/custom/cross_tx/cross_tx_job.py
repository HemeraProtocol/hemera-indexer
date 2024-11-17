import json
import logging
from collections import defaultdict

import eth_abi

from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob

from indexer.modules.custom import common_utils
from indexer.modules.custom.cross_tx.domains.feature_cross_tx import (
    L1toL2TxOnL2
)
from indexer.modules.custom.cross_tx.cross_tx_abi import (
    MINT_EVENT,
    TRANSFER_EVENT,
    APPROVAL_EVENT,
    BURN_EVENT,
    TOKENSENT_EVENT,
    TOKENRECEIVED_EVENT,
    MESSAGESENT_EVENT,
    MESSAGESTATUSCHANGED_EVENT,
    MESSAGEPROCESSED_EVENT,
    SIGNALSENT_EVENT,
)
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.rpc_utils import rpc_response_to_result, zip_rpc_response

logger = logging.getLogger(__name__)

FUNCTION_EVENT_LIST = [
    MINT_EVENT,    
    TRANSFER_EVENT,
    APPROVAL_EVENT,
    BURN_EVENT,
    TOKENSENT_EVENT,
    TOKENRECEIVED_EVENT,
    MESSAGESENT_EVENT,
    MESSAGESTATUSCHANGED_EVENT,
    MESSAGEPROCESSED_EVENT,
    SIGNALSENT_EVENT,
]
CROSS_TX_ABI = [fe.get_abi() for fe in FUNCTION_EVENT_LIST]

class CrossTXJob(FilterTransactionDataJob):
    dependency_types = [Log]
    output_types = [L1toL2TxOnL2]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self._service = kwargs["config"].get("db_service")
        self._abi_list = CROSS_TX_ABI
        self._batch_size = kwargs["batch_size"]

        config = kwargs["config"]["cross_tx_job"]
        
        #self._contract_list = [address.lower() for address in set(config.get("contract_list"))]
        
        #self._exist_pools = get_exist_pools(self._service, self._position_token_address)
        self._max_worker = kwargs["max_workers"]

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    topics=[
                        MESSAGEPROCESSED_EVENT.get_signature()
                    # todo: filter the cross tx
                    ]
                ),
            ]
        )

    #def _collect(self, **kwargs):
        

    def _process(self, **kwargs):
        # filter out transactions that are not bridge related
        logs = self._data_buff[Log.type()]
        transactions = list(filter(self.get_filter().is_satisfied_by, self._data_buff[Transaction.type()]))
        result = []
        print("check tx:", len(transactions), len(logs))
        print(transactions)