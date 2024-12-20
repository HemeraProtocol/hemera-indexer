import logging

from hemera.indexer.domains.token_transfer import ERC20TokenTransfer
from hemera.indexer.jobs import FilterTransactionDataJob
from hemera.indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from hemera.indexer.utils.abi_setting import TOKEN_TOTAL_SUPPLY_FUNCTION
from hemera.indexer.utils.multicall_hemera import Call
from hemera.indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper
from hemera_udf.total_supply.domains import Erc20CurrentTotalSupply, Erc20TotalSupply

logger = logging.getLogger(__name__)


class ExportErc20TotalSupplyJob(FilterTransactionDataJob):
    dependency_types = [ERC20TokenTransfer]
    # maybe no need Erc20CurrentTotalSupply
    output_types = [Erc20TotalSupply, Erc20CurrentTotalSupply]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        config = kwargs["config"].get("total_supply_job", {})
        self.token_address_list = config.get("token_address", [])

        self.multi_call_helper = MultiCallHelper(self._web3, kwargs, logger)

    def get_filter(self):

        return TransactionFilterByLogs(
            [
                TopicSpecification(addresses=self.token_address_list),
            ]
        )

    def _process(self, **kwargs):
        erc20_token_transfers = self._data_buff[ERC20TokenTransfer.type()]
        token_transfers = [tt for tt in erc20_token_transfers if tt.token_address in self.token_address_list]
        call_dict = {}
        for token_transfer in token_transfers:
            token_address = token_transfer.token_address
            block_number = token_transfer.block_number
            call = Call(
                target=token_address,
                function_abi=TOKEN_TOTAL_SUPPLY_FUNCTION,
                block_number=block_number,
                user_defined_k=token_transfer.block_timestamp,
            )
            call_dict[token_address, block_number] = call

        call_list = list(call_dict.values())

        self.multi_call_helper.execute_calls(call_list)

        records = []
        current_dict = {}

        call_list.sort(key=lambda call: call.block_number)

        for call in call_list:
            if call.returns:
                total_supply = call.returns.get("totalSupply")

                token_address = call.target.lower()
                erc_total_supply = Erc20TotalSupply(
                    token_address=token_address,
                    total_supply=total_supply,
                    block_number=call.block_number,
                    block_timestamp=call.user_defined_k,
                )

                current_dict[token_address] = Erc20CurrentTotalSupply(**vars(erc_total_supply))
                records.append(erc_total_supply)
        self._collect_domains(records)
        self._collect_domains(current_dict.values())
