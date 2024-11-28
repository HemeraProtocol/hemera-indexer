import logging

from indexer.domain.token_transfer import ERC20TokenTransfer
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.total_supply.domain.erc20_total_supply import Erc20CurrentTotalSupply, Erc20TotalSupply
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.abi_setting import TOKEN_TOTAL_SUPPLY_FUNCTION
from indexer.utils.multicall_hemera import Call
from indexer.utils.multicall_hemera.multi_call_helper import MultiCallHelper

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
        token_transfers = self._data_buff[ERC20TokenTransfer.type()]
        call_list = []
        for token_transfer in token_transfers:
            call = Call(
                target=token_transfer.token_address,
                function_abi=TOKEN_TOTAL_SUPPLY_FUNCTION,
                block_number=token_transfer.block_number,
                user_defined_k=token_transfer.block_timestamp,
            )
            call_list.append(call)
        self.multi_call_helper.execute_calls(call_list)

        records = []
        current_dict = {}

        for call in call_list:
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
