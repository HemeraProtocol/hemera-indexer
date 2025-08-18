import logging

from hemera.indexer.domains.token_transfer import ERC20TokenTransfer
from hemera.indexer.jobs.base_job import FilterTransactionDataJob
from hemera.indexer.specification.specification import TransactionFilterByLogs, TopicSpecification
from hemera.indexer.utils.multicall_hemera import Call
from hemera.indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper
from hemera_udf.spectra.abi.abi import GET_BALANCES_FUNCTION
from hemera_udf.spectra.domains import SpectraLpBalance

logger = logging.getLogger(__name__)


class ExportSpectraLpBalance(FilterTransactionDataJob):
    dependency_types = [ERC20TokenTransfer]

    output_types = [SpectraLpBalance]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multi_call_helper = MultiCallHelper(self._web3, kwargs, logger)
        self.lp_address = '0x1dc93df5d77b705c8c16527ec800961f1a7b3413'

        self.token0_address = '0xb74e4f4add805a7191a934a05d3a826e8d714a44'
        self.token1_address = '0x40defb4b2a451c7bad7c256132085ac4348c3b4c'


    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    addresses=[str(self.lp_address)],
                ),
            ]
        )

    def _process(self, **kwargs):
        erc_20_token_transfers = self._data_buff[ERC20TokenTransfer.type()]
        lp_token_transfers = [
            tt for tt in erc_20_token_transfers if tt.token_address in self.lp_address
        ]

        call_dict = {}
        for token_transfer in lp_token_transfers:
            block_number = token_transfer.block_number
            call = Call(
                target=self.lp_address,
                function_abi=GET_BALANCES_FUNCTION,
                block_number=block_number,
                user_defined_k=token_transfer.block_timestamp,
            )
            call_dict[block_number] = call

        call_list = list(call_dict.values())

        self.multi_call_helper.execute_calls(call_list)

        records = []

        call_list.sort(key=lambda call: call.block_number)

        for call in call_list:
            returns = call.returns
            if returns:
                token0_balance, token1_balance = returns.get("")
                domain = SpectraLpBalance(
                    token0_address=self.token0_address,
                    token1_address=self.token1_address,
                    token0_balance=token0_balance,
                    token1_balance=token1_balance,
                    block_number=call.block_number,
                    block_timestamp=call.user_defined_k,
                )

                records.append(domain)
        self._collect_domains(records)
