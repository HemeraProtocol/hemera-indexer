import json
import numpy
import pandas

from web3 import Web3

from domain.token_balance import format_token_balance_data
from domain.token_holder import format_erc20_token_holder_data, format_erc721_token_holder_data, \
    format_erc1155_token_holder_data
from exporters.console_item_exporter import ConsoleItemExporter
from jobs.base_job import BaseJob
from executors.batch_work_executor import BatchWorkExecutor
from utils.enrich import enrich_blocks_timestamp
from utils.json_rpc_requests import generate_get_token_balance_json_rpc
from utils.utils import rpc_response_to_result
from utils.web3_utils import verify_0_address

contract_abi = {
    "ERC20": [
        {
            "constant": True,
            "inputs": [
                {
                    "name": "_owner",
                    "type": "address"
                }
            ],
            "name": "balanceOf",
            "outputs": [
                {
                    "name": "balance",
                    "type": "uint256"
                }
            ],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ],
    "ERC721": [
        {
            "constant": True,
            "inputs": [
                {
                    "name": "owner",
                    "type": "address"
                }
            ],
            "name": "balanceOf",
            "outputs": [
                {
                    "name": "balance",
                    "type": "uint256"
                }
            ],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ],
    "ERC1155": [
        {
            "constant": True,
            "inputs": [
                {
                    "name": "account",
                    "type": "address"
                },
                {
                    "name": "id",
                    "type": "uint256"
                }
            ],
            "name": "balanceOf",
            "outputs": [
                {
                    "name": "balance",
                    "type": "uint256"
                }
            ],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ]
}


# Exports token balance
class ExportTokenBalancesAndHoldersJob(BaseJob):
    def __init__(
            self,
            index_keys,
            web3,
            batch_size,
            batch_web3_provider,
            max_workers,
            item_exporter=ConsoleItemExporter()):
        super().__init__(index_keys)
        self._web3 = web3
        self._batch_web3_provider = batch_web3_provider
        self._batch_work_executor = BatchWorkExecutor(batch_size, max_workers)
        self._item_exporter = item_exporter

    def _start(self):
        super()._start()

    def _collect(self):
        origin_parameters = []

        for transfer in self._data_buff['token_transfer']:
            from_address = Web3.to_checksum_address(transfer['fromAddress'])
            to_address = Web3.to_checksum_address(transfer['toAddress'])
            token_address = Web3.to_checksum_address(transfer['tokenAddress'])

            origin_parameters.append({
                'address': from_address,
                'token_address': token_address,
                'token_id': transfer['tokenId'],
                'token_type': transfer['tokenType'],
                'block_number': transfer['blockNumber'],
            })
            origin_parameters.append({
                'address': to_address,
                'token_address': token_address,
                'token_id': transfer['tokenId'],
                'token_type': transfer['tokenType'],
                'block_number': transfer['blockNumber'],
            })

        rpc_parameters = []
        for parameter in pandas.DataFrame(origin_parameters).drop_duplicates().replace(numpy.NaN, None).to_dict(
                orient='records'):
            parameter['token_id'] = int(parameter['token_id']) if parameter['token_id'] is not None else None
            if not verify_0_address(parameter['address']):
                contract = self._web3.eth.contract(address=parameter['token_address'],
                                                   abi=contract_abi[parameter['token_type']])

                if len(contract_abi[parameter['token_type']][0]['inputs']) > 1:
                    data = contract.encodeABI(fn_name='balanceOf', args=[parameter['address'], parameter['token_id']])
                else:
                    data = contract.encodeABI(fn_name='balanceOf', args=[parameter['address']])

                rpc_parameters.append({
                    'address': parameter['address'],
                    'token_address': parameter['token_address'],
                    'token_id': parameter['token_id'],
                    'token_type': parameter['token_type'],
                    'data': data,
                    'block_number': parameter['block_number'],
                })

        self._batch_work_executor.execute(rpc_parameters, self._collect_batch)

    def _collect_batch(self, parameters):
        token_balance_rpc = list(generate_get_token_balance_json_rpc(parameters))
        response = self._batch_web3_provider.make_batch_request(json.dumps(token_balance_rpc))

        for data in list(zip(parameters, response)):
            result = rpc_response_to_result(data[1])
            token_balance = {
                'item': 'token_balance',
                'tokenId': data[0]['token_id'],
                'address': data[0]['address'],
                'tokenAddress': data[0]['token_address'],
                'tokenType': data[0]['token_type'],
                'tokenBalance': int(result, 16),
                'blockNumber': data[0]['block_number'],
            }

            self._collect_item(token_balance)

    def _process(self):
        self._data_buff['enriched_token_balances'] = [format_token_balance_data(token_balance)
                                                      for token_balance in
                                                      enrich_blocks_timestamp(self._data_buff['block'],
                                                                              self._data_buff['token_balance'])]

        self._data_buff['enriched_token_balances'] = sorted(self._data_buff['enriched_token_balances'],
                                                            key=lambda x: (x['block_number'], x['address']))

        total_erc20, total_erc721, total_erc1155 = [], [], []
        for token_balance in self._data_buff['enriched_token_balances']:
            if token_balance['token_type'] == "ERC20":
                total_erc20.append(format_erc20_token_holder_data(token_balance))
            elif token_balance['token_type'] == "ERC721":
                total_erc721.append(format_erc721_token_holder_data(token_balance))
            elif token_balance['token_type'] == "ERC1155":
                total_erc1155.append(format_erc1155_token_holder_data(token_balance))

        if len(total_erc20) > 0:
            total_erc20_frame = pandas.DataFrame(total_erc20)
            self._data_buff['erc20_token_holders'] = total_erc20_frame.loc[total_erc20_frame.groupby(
                ['token_address', 'wallet_address'])['block_number'].idxmax()].to_dict(orient='records')

        if len(total_erc721) > 0:
            total_erc721_frame = pandas.DataFrame(total_erc721)
            self._data_buff['erc721_token_holders'] = total_erc721_frame.loc[total_erc721_frame.groupby(
                ['token_address', 'wallet_address'])['block_number'].idxmax()].to_dict(orient='records')

        if len(total_erc1155) > 0:
            total_erc1155_frame = pandas.DataFrame(total_erc1155)
            self._data_buff['erc1155_token_holders'] = total_erc1155_frame.loc[total_erc1155_frame.groupby(
                ['token_address', 'wallet_address', 'token_id'])['block_number'].idxmax()].to_dict(orient='records')

    def _export(self):
        items = self._extract_from_buff(
            ['enriched_token_balances', 'erc20_token_holders', 'erc721_token_holders', 'erc1155_token_holders'])
        self._item_exporter.export_items(items)

    def _end(self):
        self._batch_work_executor.shutdown()
        super()._end()
