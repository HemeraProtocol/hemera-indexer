import json

from web3 import Web3

from jobs.base_job import BaseJob
from executors.batch_work_executor import BatchWorkExecutor
from utils.json_rpc_requests import generate_get_token_balance_json_rpc
from utils.utils import rpc_response_to_result, hex_to_dec

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
class ExportTokenBalancesJob(BaseJob):
    def __init__(
            self,
            token_transfer_iterable,
            batch_size,
            batch_web3_provider,
            web3,
            max_workers,
            index_keys):

        self.token_transfer_iterable = token_transfer_iterable
        self.batch_web3_provider = batch_web3_provider
        self.web3 = web3
        self.batch_work_executor = BatchWorkExecutor(batch_size, max_workers)
        self.index_keys = index_keys

        distinct_addresses = set()
        for transfer in self.token_transfer_iterable:
            from_address = Web3.to_checksum_address(transfer['fromAddress'])
            to_address = Web3.to_checksum_address(transfer['toAddress'])
            token_address = Web3.to_checksum_address(transfer['tokenAddress'])

            distinct_addresses.add((from_address, token_address, transfer['tokenId'],
                                    transfer['blockNumber'], transfer['tokenType']))
            distinct_addresses.add((to_address, token_address, transfer['tokenId'],
                                    transfer['blockNumber'], transfer['tokenType']))

        self.rpc_parameters = []
        for address in list(distinct_addresses):
            contract = self.web3.eth.contract(address=address[1], abi=contract_abi[address[4]])
            data = contract.encodeABI(fn_name='balanceOf', args=[address[0]])
            self.rpc_parameters.append({
                'token_id': address[2],
                'address': address[0],
                'token_address': address[1],
                'token_type': address[4],
                'data': data,
                'block_number': address[3],
            })

    def _start(self):
        super()._start()

    def _export(self):
        self.batch_work_executor.execute(self.rpc_parameters, self._export_batch)

    def _export_batch(self, parameters):
        token_balance_rpc = list(generate_get_token_balance_json_rpc(parameters))
        response = self.batch_web3_provider.make_batch_request(json.dumps(token_balance_rpc))

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

            self._export_item(token_balance)

    def _end(self):
        self.batch_work_executor.shutdown()
        self.data_buff['token_balance'] = sorted(self.data_buff['token_balance'],
                                                 key=lambda x: (hex_to_dec(x['blockNumber']), x['address']))
