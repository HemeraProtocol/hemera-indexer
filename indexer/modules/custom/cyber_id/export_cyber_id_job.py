import logging
from itertools import groupby
from typing import List

from web3 import Web3

from indexer.domain.log import Log
from indexer.domain.transaction import Transaction
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.cyber_id.cyber_abi import abi_map
from indexer.modules.custom.cyber_id.cyber_domain import CyberAddressD, CyberIDRegisterD, CyberAddressChangedD
from indexer.modules.custom.cyber_id.utils import get_reverse_node, get_node
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)

CyberIdReverseRegistrarContractAddress = "0x79502da131357333d61c39b7411d01df54591961"
CyberIdPublicResolverContractAddress = "0xfb2f304c1fcd6b053ee033c03293616d5121944b"
CyberIdTokenContractAddress = "0xc137be6b59e824672aada673e55cf4d150669af8"
NameChangedTopic = "0xb7d29e911041e8d9b843369e890bcb72c9388692ba48b65ac54e7214c4c348f7"
RegisterTopic = "0xa50d98082663c2b716ab4f8b6b2a51fcaed7eae222cd3d74b19de4691ede728a"
AddressChangedTopic = "0x65412581168e88a1e60c6459d7f44ae83ad0832e670826c05a4e2476b57af752"


class ExportCyberIDJob(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [CyberAddressD, CyberIDRegisterD, CyberAddressChangedD]
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
                [TopicSpecification(addresses=[CyberIdPublicResolverContractAddress, CyberIdTokenContractAddress],
                                    topics=[NameChangedTopic, RegisterTopic])]
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
                        address=decoded_input[1].get("addr").lower(),
                        name=decoded_input[1].get("name"),
                        block_number=transaction.block_number,
                        reverse_node=get_reverse_node(decoded_input[1].get("addr")),
                    )
                    self._collect_item(cyber_address.type(), cyber_address)
                if func_name == "setName":
                    decoded_input = self.decode_transaction(transaction)
                    cyber_address = CyberAddressD(
                        address=transaction.from_address.lower(),
                        name=decoded_input[1].get("name"),
                        block_number=transaction.block_number,
                        reverse_node=get_reverse_node(transaction.from_address),
                    )
                    self._collect_item(cyber_address.type(), cyber_address)
        logs: List[Log] = self._data_buff.get(Log.type(), [])
        for log in logs:
            if log.address.lower() == CyberIdTokenContractAddress and log.topic0 == RegisterTopic:
                decoded_data = self.w3.codec.decode(['string', 'uint256'], bytes.fromhex(log.data[2:]))
                cid = decoded_data[0]
                cyber_address = CyberIDRegisterD(
                    label=cid,
                    token_id=log.topic3,
                    cost=int(decoded_data[1]),
                    block_number=log.block_number,
                    node=get_node(cid+".cyber"),
                    registration=log.block_timestamp
                )
                self._collect_item(cyber_address.type(), cyber_address)
            if log.address.lower() == CyberIdPublicResolverContractAddress and log.topic0 == AddressChangedTopic:
                decoded_data = self.w3.codec.decode(['uint256', 'bytes'], bytes.fromhex(log.data[2:]))
                address_change_d = CyberAddressChangedD(
                    node=log.topic1,
                    address='0x'+decoded_data[1].hex(),
                    block_number=log.block_number
                )
                self._collect_item(address_change_d.type(), address_change_d)

    def _process(self, **kwargs):
        cyber_addresses = self._data_buff.get(CyberAddressD.type(), [])
        cyber_addresses.sort(key=lambda x: (x.address, x.block_number))
        self._data_buff[CyberAddressD.type()] = [
            list(group)[-1] for key, group in groupby(cyber_addresses, key=lambda x: x.address)
        ]

        address_changes = self._data_buff.get(CyberAddressChangedD.type(), [])
        address_changes.sort(key=lambda x: (x.node, x.block_number))
        self._data_buff[CyberAddressChangedD.type()] = [
            list(group)[-1] for key, group in groupby(address_changes, key=lambda x: x.node)
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
