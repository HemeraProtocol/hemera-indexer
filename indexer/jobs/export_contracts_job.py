import json
import logging
from typing import List

from web3 import Web3
from eth_abi import abi

from indexer.domain.contract import extract_contract_from_trace, Contract
from enumeration.entity_type import EntityType
from indexer.domain.contract_internal_transaction import ContractInternalTransaction
from indexer.domain.trace import Trace
from indexer.exporters.console_item_exporter import ConsoleItemExporter
from indexer.jobs.base_job import BaseJob
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.utils.json_rpc_requests import generate_eth_call_json_rpc
from indexer.utils.utils import rpc_response_to_result, zip_rpc_response

logger = logging.getLogger(__name__)
contract_abi = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [
            {
                "name": "",
                "type": "string"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]


# Exports contracts
class ExportContractsJob(BaseJob):

    dependency_types = [Trace]
    output_types = [Contract]

    def __init__(
            self,
            **kwargs
    ):
        super().__init__(**kwargs)

        self._batch_work_executor = BatchWorkExecutor(
            kwargs['batch_size'], kwargs['max_workers'],
            job_name=self.__class__.__name__
        )
        self._is_batch = kwargs['batch_size'] > 1


    def _start(self):
        super()._start()

    def _collect(self, **kwargs):
        contracts = build_contracts(self._web3, self._data_buff[Trace.type()])

        self._batch_work_executor.execute(contracts, self._collect_batch, total_items=len(contracts))
        self._batch_work_executor.shutdown()

    def _collect_batch(self, contracts):
        contracts = contract_info_rpc_requests(self._batch_web3_provider.make_request, contracts, self._is_batch)

        for contract in contracts:
            self._collect_item(Contract.type(), Contract(contract))

    def _process(self):
        self._data_buff[Contract.type()].sort(
            key=lambda x: (x.block_number,
                           x.transaction_index,
                           x.address))



def build_contracts(web3, traces: List[Trace]):
    contracts = []
    for trace in traces:
        if trace.trace_type in ['create', 'create2'] and trace.to_address is not None \
                and len(trace.to_address) > 0 and trace.status == 1:
            contract = extract_contract_from_trace(trace)
            contract['param_to'] = contract['address']

            try:
                contract['param_data'] = (web3.eth
                                          .contract(address=Web3.to_checksum_address(contract['address']),
                                                    abi=contract_abi)
                                          .encodeABI(fn_name='name'))
            except Exception as e:
                logger.warning(f"Encoding contract api parameter failed. "
                               f"contract address: {contract['address']}. "
                               f"fn: name. "
                               f"exception: {e}. ")
                contract['param_data'] = '0x'

            contract['param_number'] = hex(contract['block_number'])
            contracts.append(contract)

    return contracts


def contract_info_rpc_requests(make_requests, contracts, is_batch):
    for idx, contract in enumerate(contracts):
        contract['request_id'] = idx

    contract_name_rpc = list(generate_eth_call_json_rpc(contracts))

    if is_batch:
        response = make_requests(params=json.dumps(contract_name_rpc))
    else:
        response = [make_requests(params=json.dumps(contract_name_rpc[0]))]

    for data in list(zip_rpc_response(contracts, response)):
        result = rpc_response_to_result(data[1], ignore_errors=True)
        contract = data[0]
        info = result[2:] if result is not None else None

        try:
            contract['name'] = abi.decode(['string'], bytes.fromhex(info))[0].replace('\u0000', '')
        except Exception as e:
            logger.warning(f"Decoding contract name failed. "
                           f"contract address: {contract['address']}. "
                           f"rpc response: {result}. "
                           f"exception: {e}")
            contract['name'] = None

    return contracts
