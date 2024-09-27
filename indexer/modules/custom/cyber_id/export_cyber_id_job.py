import logging
from itertools import groupby 
from typing import List

from web3 import Web3

from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.cyber_id.cyber_abi import abi_map
from indexer.modules.custom.cyber_id.cyber_domain import CyberAddressD
from indexer.modules.custom.cyber_id.utils import get_reverse_node
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)

CyberIdReverseRegistrarContractAddress = "0x79502da131357333d61c39b7411d01df54591961"
CyberIdPublicResolverContractAddress = "0xfb2f304c1fcd6b053ee033c03293616d5121944b"
NameChangedTopic = "0xb7d29e911041e8d9b843369e890bcb72c9388692ba48b65ac54e7214c4c348f7"


class ExportCyberIDJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [CyberAddressD]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._is_batch = kwargs["batch_size"] > 1
        self._filters = kwargs.get("filters", [])
        self.contract_object_map = {}
        self.func_name_map = {}
        self.w3 = Web3(Web3.HTTPProvider(self._web3.provider.endpoint_uri))
        for ad_lower in abi_map:
            abi = abi_map[ad_lower]
            contract = self.w3.eth.contract(address=Web3.to_checksum_address(ad_lower), abi=abi)
            self.contract_object_map[ad_lower] = contract
        for contract_address, contract in self.contract_object_map.items():
            if not contract:
                continue
            functions = [abi for abi in contract.abi if abi["type"] == "function"]
            for function in functions:
                sig = self.get_function_signature(function)
                self.func_name_map[sig[0:10]] = function

    def get_filter(self):

        return [
            TransactionFilterByLogs(
                [TopicSpecification(addresses=[CyberIdPublicResolverContractAddress], topics=[NameChangedTopic])]
            ),
        ]

    def _collect(self, **kwargs):
        transactions: List[Transaction] = self._data_buff.get(Transaction.type(), [])
        for transaction in transactions:
            if transaction.to_address.lower() == CyberIdReverseRegistrarContractAddress:
                func_name = self.func_name_map.get(transaction.input[0:10], {}).get("name")
                if func_name == "setNameForAddr":
                    decoded_input = self.decode_transaction(transaction)
                    cyber_address = CyberAddressD(
                        address=decoded_input[1].get("addr"),
                        name=decoded_input[1].get("name"),
                        block_number=transaction.block_number,
                        reverse_node=get_reverse_node(decoded_input[1].get("addr")),
                    )
                    self._collect_item(cyber_address.type(), cyber_address)
                if func_name == "setName":
                    decoded_input = self.decode_transaction(transaction)
                    cyber_address = CyberAddressD(
                        address=transaction.from_address,
                        name=decoded_input[1].get("name"),
                        block_number=transaction.block_number,
                        reverse_node=get_reverse_node(transaction.from_address),
                    )
                    self._collect_item(cyber_address.type(), cyber_address)

    def _process(self, **kwargs):
        cyber_addresses = self._data_buff.get(CyberAddressD.type(), [])

        cyber_addresses.sort(key=lambda x: (x.address, x.block_number))

        self._data_buff[CyberAddressD.type()] = [
            list(group)[-1] for key, group in groupby(cyber_addresses, key=lambda x: x.address)
        ]

    def decode_transaction(self, transaction):
        if not transaction.to_address:
            return None
        con = self.contract_object_map[transaction.to_address]
        decoded_input = con.decode_function_input(transaction.input)
        return decoded_input

    def get_function_signature(self, function_abi):
        name = function_abi["name"]
        inputs = [input["type"] for input in function_abi["inputs"]]
        signature = f"{name}({','.join(inputs)})"
        sig = self.w3.to_hex(Web3.keccak(text=signature))
        return sig
