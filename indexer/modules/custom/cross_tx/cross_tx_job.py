import json
import logging
from collections import defaultdict
from web3 import Web3


import eth_abi

from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob

from indexer.modules.custom import common_utils
from indexer.modules.custom.cross_tx.domains.feature_cross_tx import (
    L1toL2TxOnL2,
    L2toL1TxOnL2
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

from indexer.utils.abi_setting import TOKEN_SYMBOL_FUNCTION
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
    output_types = [L1toL2TxOnL2, L2toL1TxOnL2]
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
        self._contract_dict = {k: v.lower() for k, v in config.get("contract_dict").items()}
        
        self._max_worker = kwargs["max_workers"]

    def get_filter(self):
        # now filter L1 to L2 event, todo: L2 to L1
        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    topics=[
                        MESSAGEPROCESSED_EVENT.get_signature(),
                        MESSAGESENT_EVENT.get_signature()
                    # todo: filter the cross tx
                    ]
                ),
            ]
        )

    def _collect(self, **kwargs):
        # filter out transactions that are not bridge related
        logs = self._data_buff[Log.type()]
        transactions = list(filter(self.get_filter().is_satisfied_by, self._data_buff[Transaction.type()]))
        result = []
        l1tol2 = []
        l2tol1 = []
        for tnx in transactions:
            token_address = ""
            token_id = "ETH"
            amount = 0
            for log in tnx.receipt.logs:
                if log.topic0 == TOKENRECEIVED_EVENT.get_signature():
                    data_0 = TOKENRECEIVED_EVENT.decode_log(log)
                    token_address = data_0['token']
                    token_id = get_token(self._web3, self._abi_list, token_address)
                    amount = data_0['amount']
                    
                if log.topic0 == TOKENSENT_EVENT.get_signature():
                    data_0 = TOKENSENT_EVENT.decode_log(log)
                    token_address = data_0['token']
                    token_id = get_token(self._web3, self._abi_list, token_address)
                    amount = data_0['amount']
            
            for log in tnx.receipt.logs:
                if log.topic0 == MESSAGEPROCESSED_EVENT.get_signature():
                    data_0 = MESSAGEPROCESSED_EVENT.decode_log(log)
                    if amount == 0:
                        amount = data_0['message']['value']
                    dt = L1toL2TxOnL2(transaction_hash=tnx.hash,
                                      fee=data_0['message']['fee'],
                                      src_chain_id=data_0['message']['srcChainId'],
                                      dest_chain_id=data_0['message']['destChainId'],
                                      src_owner=data_0['message']['srcOwner'],
                                      dest_owner=data_0['message']['destOwner'],
                                      token_id=token_id,
                                      token_address=token_address,
                                      amount = amount,
                                      block_number=tnx.block_number, 
                                      block_timestamp=tnx.block_timestamp)
                    l1tol2.append(dt)
                
                if log.topic0 == MESSAGESENT_EVENT.get_signature():
                    data_0 = MESSAGESENT_EVENT.decode_log(log)
                    if amount == 0:
                        amount = data_0['message']['value']
                    dt = L2toL1TxOnL2(transaction_hash=tnx.hash,
                                      fee=data_0['message']['fee'],
                                      src_chain_id=data_0['message']['srcChainId'],
                                      dest_chain_id=data_0['message']['destChainId'],
                                      src_owner=data_0['message']['srcOwner'],
                                      dest_owner=data_0['message']['destOwner'],
                                      token_id=token_id,
                                      token_address=token_address,
                                      amount = amount,
                                      block_number=tnx.block_number, 
                                      block_timestamp=tnx.block_timestamp)
                    l2tol1.append(dt)
        # todo: l1tol2
        result += l1tol2
        result += l2tol1
        for data in result:
            #print(data.type(), data)
            self._collect_item(data.type(), data)
            
    def _process(self, **kwargs):
        self._data_buff[L1toL2TxOnL2.type()].sort(key=lambda x: x.block_number)
        self._data_buff[L2toL1TxOnL2.type()].sort(key=lambda x: x.block_number)
                

        
def get_token(web3, abi_list, token_address) :
    contract = web3.eth.contract(address= Web3.to_checksum_address(token_address), abi=[TOKEN_SYMBOL_FUNCTION.get_abi()])
    return contract.functions.symbol().call()

    