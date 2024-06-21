import json

from eth_abi.exceptions import InsufficientDataBytes, InvalidPointer
from web3 import Web3
from eth_abi import abi

from domain.contract import extract_contract_from_trace, format_contract_data
from enumeration.entity_type import EntityType
from exporters.console_item_exporter import ConsoleItemExporter
from jobs.base_job import BaseJob
from executors.batch_work_executor import BatchWorkExecutor
from utils.enrich import enrich_contracts
from utils.json_rpc_requests import generate_eth_call_json_rpc
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


# Exports contracts
class ExportContractsJob(BaseJob):
    def __init__(
            self,
            index_keys,
            entity_types,
            web3,
            batch_web3_provider,
            batch_size,
            max_workers,
            item_exporter=ConsoleItemExporter()):
        super().__init__(index_keys=index_keys, entity_types=entity_types)
        self._web3 = web3
        self._batch_web3_provider = batch_web3_provider
        self._batch_work_executor = BatchWorkExecutor(batch_size, max_workers)
        self._item_exporter = item_exporter

    def _start(self):
        super()._start()

    def _collect(self):
        contracts = []
        for trace_dict in self._data_buff['trace']:
            if trace_dict['trace_type'] in ['create', 'create2'] and trace_dict['to_address'] is not None \
                    and len(trace_dict['to_address']) > 0 and trace_dict['status'] == 1:
                contract = extract_contract_from_trace(trace_dict)
                contract['param_to'] = contract['address']
                contract['param_data'] = (self._web3.eth
                                          .contract(address=Web3.to_checksum_address(contract['address']),
                                                    abi=contract_abi)
                                          .encodeABI(fn_name='name'))
                contract['param_number'] = hex(contract['block_number'])
                contracts.append(contract)

        self._batch_work_executor.execute(contracts, self._collect_batch)

    def _collect_batch(self, contracts):
        contract_name_rpc = list(generate_eth_call_json_rpc(contracts, is_latest=False))
        response = self._batch_web3_provider.make_batch_request(json.dumps(contract_name_rpc))

        for data in list(zip(contracts, response)):
            result = rpc_response_to_result(data[1], ignore_errors=True)
            contract = data[0]
            contract['item'] = 'contract'
            info = result[2:] if result is not None else None
            try:
                contract['name'] = abi.decode(['string'], bytes.fromhex(info))[0].replace('\u0000', '')
            except (InsufficientDataBytes, InvalidPointer, TypeError) as e:
                contract['name'] = None

            self._collect_item(contract)

    def _process(self):
        self._data_buff['enriched_contract'] = [format_contract_data(contract) for contract in
                                                enrich_contracts(self._data_buff['formated_block'],
                                                                 self._data_buff['contract'])]

        self._data_buff['enriched_contract'] = sorted(self._data_buff['enriched_contract'],
                                                      key=lambda x: (x['block_number'],
                                                                     x['transaction_index'],
                                                                     x['address']))

    def _export(self):
        if self._entity_types & EntityType.CONTRACT:
            items = self._extract_from_buff(['enriched_contract'])
            self._item_exporter.export_items(items)

    def _end(self):
        self._batch_work_executor.shutdown()
        super()._end()
