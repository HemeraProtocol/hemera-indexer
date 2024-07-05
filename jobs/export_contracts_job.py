import json
import logging

from web3 import Web3
from eth_abi import abi

from domain.contract import extract_contract_from_trace, format_contract_data
from enumeration.entity_type import EntityType
from exporters.console_item_exporter import ConsoleItemExporter
from jobs.base_job import BaseJob
from executors.batch_work_executor import BatchWorkExecutor
from services.rpc_statistic_service import statistic_service
from utils.enrich import enrich_contracts
from utils.json_rpc_requests import generate_eth_call_json_rpc
from utils.utils import rpc_response_to_result, zip_rpc_response

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
        self._batch_work_executor = BatchWorkExecutor(batch_size, max_workers, job_name=self.__class__.__name__)
        self._is_batch = batch_size > 1
        self._item_exporter = item_exporter

    def _start(self):
        super()._start()

    def _collect(self):
        contracts = build_contracts(self._web3, self._data_buff['trace'])

        self._batch_work_executor.execute(contracts, self._collect_batch, total_items=len(contracts))
        self._batch_work_executor.shutdown()

    def _collect_batch(self, contracts):
        contracts = contract_info_rpc_requests(self._batch_web3_provider.make_request, contracts, self._is_batch)

        for contract in contracts:
            contract['item'] = 'contract'
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


def build_contracts(web3, traces):
    contracts = []
    for trace_dict in traces:
        if trace_dict['trace_type'] in ['create', 'create2'] and trace_dict['to_address'] is not None \
                and len(trace_dict['to_address']) > 0 and trace_dict['status'] == 1:
            contract = extract_contract_from_trace(trace_dict)
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

    contract_name_rpc = list(generate_eth_call_json_rpc(contracts, is_latest=False))

    if is_batch:
        response = make_requests(params=json.dumps(contract_name_rpc))
    else:
        response = [make_requests(params=json.dumps(contract_name_rpc[0]))]

    statistic_service.increase_rpc_count(method='eth_call',
                                         caller=__name__,
                                         count=len(contract_name_rpc))

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
