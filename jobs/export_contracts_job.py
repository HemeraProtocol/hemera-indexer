import json

from eth_abi.exceptions import InsufficientDataBytes
from web3 import Web3
from eth_abi import abi

from domain.contract import extract_contract_from_trace
from jobs.base_job import BaseJob
from executors.batch_work_executor import BatchWorkExecutor
from utils.json_rpc_requests import generate_get_contract_name_json_rpc
from utils.utils import rpc_response_to_result

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


# Exports token balance
class ExportContractsJob(BaseJob):
    def __init__(
            self,
            traces_iterable,
            batch_size,
            batch_web3_provider,
            web3,
            max_workers,
            index_keys):
        self.traces_iterable = traces_iterable
        self.batch_web3_provider = batch_web3_provider
        self.web3 = web3
        self.batch_work_executor = BatchWorkExecutor(batch_size, max_workers)
        self.index_keys = index_keys

        self.contracts = []
        for trace_dict in traces_iterable:
            if trace_dict['trace_type'] in ['create', 'create2'] and trace_dict['to_address'] is not None \
                    and len(trace_dict['to_address']) > 0 and trace_dict['status'] == 1:
                contract = extract_contract_from_trace(trace_dict)
                contract['data'] = (self.web3.eth
                                    .contract(address=Web3.to_checksum_address(contract['address']), abi=contract_abi)
                                    .encodeABI(fn_name='name'))
                self.contracts.append(contract)

    def _start(self):
        super()._start()

    def _export(self):
        self.batch_work_executor.execute(self.contracts, self._export_batch)

    def _export_batch(self, contracts):
        contract_name_rpc = list(generate_get_contract_name_json_rpc(contracts))
        response = self.batch_web3_provider.make_batch_request(json.dumps(contract_name_rpc))

        for data in list(zip(contracts, response)):
            result = rpc_response_to_result(data[1], ignore_errors=True)
            contract = data[0]
            contract['item'] = 'contract'
            name = result[2:] if result is not None else ''
            try:
                contract['name'] = abi.decode(['string'], bytes.fromhex(name))[0]
            except InsufficientDataBytes:
                contract['name'] = ''

            self._export_item(contract)

    def _end(self):
        self.batch_work_executor.shutdown()
        self.data_buff['contract'] = sorted(self.data_buff['contract'],
                                            key=lambda x: (x['block_number'],
                                                           x['transaction_index'],
                                                           x['address']))
