# import logging
# from typing import List

# from indexer.domain.log import Log
# from indexer.domain.transaction import Transaction
# from indexer.jobs.base_job import FilterTransactionDataJob
# from indexer.modules.custom.erc721_token_mint.domain.erc721_mint_time import ERC721TokenMint
# from indexer.utils.multicall_hemera.util import calculate_execution_time
# from indexer.utils.utils import ZERO_ADDRESS
# from indexer.domain.token_transfer import (
#     StoryIpRegister,
#     extract_ip_register,
#     register_event,
# )
# from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

# logger = logging.getLogger(__name__)

# # Constants
# TARGET_TOKEN_ADDRESS = ["0x1a9d0d28a0422F26D31Be72Edc6f13ea4371E11B"]

# def _filter_mint_tokens(logs: List[Log]) -> List[StoryIpRegister]:
#     token_transfers = []
#     for log in logs:
#         token_transfers += extract_ip_register(log)
#     # return [transfer for transfer in token_transfers if
#     #         transfer.from_address == ZERO_ADDRESS and transfer.token_type == "ERC721"]
#     # print(token_transfers)
#     return token_transfers


# class ExportERC721MintTimeJob(FilterTransactionDataJob):
#     dependency_types = [Transaction]
#     output_types = [ERC721TokenMint]
#     able_to_reorg = True

#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)

#     @calculate_execution_time
#     def _collect(self, **kwargs):
#         logs = self._data_buff[Log.type()]
#         mint_tokens = _filter_mint_tokens(logs)

#         erc721_mint_infos = [
#             ERC721TokenMint(
#                 ip_account=StoryIpRegister.ip_account,
#                 nft_contract=StoryIpRegister.token_contract,
#                 nft_id=StoryIpRegister.token_id,
#                 chain_id=StoryIpRegister.chain_id,
#                 block_number=StoryIpRegister.block_number,
#                 transaction_hash=StoryIpRegister.transaction_hash
#             ) for StoryIpRegister in mint_tokens
#         ]
#         print(erc721_mint_infos)
#         self._collect_domains(erc721_mint_infos)

#     def _process(self, **kwargs):
#         pass
#         print(self._data_buff[ERC721TokenMint.type()])

#     def get_filter(self):
#         topic_filter_list = [
#             TopicSpecification(
#                 addresses=TARGET_TOKEN_ADDRESS, topics=[register_event.get_signature()]
#             )
#         ]

#         return TransactionFilterByLogs(topic_filter_list)
