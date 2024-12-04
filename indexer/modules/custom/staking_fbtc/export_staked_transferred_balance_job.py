import logging
from collections import defaultdict

from common.utils.format_utils import bytes_to_hex_str
from sqlalchemy import text

from indexer.domain.token_transfer import ERC20TokenTransfer
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom.staking_fbtc.domain.af_staked_transferred_balance import (
    AfStakedTransferredBalanceCurrentDomain,
    AfStakedTransferredBalanceHistDomain,
)
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from indexer.utils.collection_utils import distinct_collections_by_group

logger = logging.getLogger(__name__)


class ExportTransferredBalanceJob(FilterTransactionDataJob):
    dependency_types = [ERC20TokenTransfer]
    output_types = [AfStakedTransferredBalanceHistDomain, AfStakedTransferredBalanceCurrentDomain]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        config = kwargs["config"]
        self._service = config.get("db_service")
        job_config = config.get("export_staked_transferred_balance_job")
        transferred_contracts_dict = job_config.get("TRANSFERRED_CONTRACTS_DICT")
        self.address_protocol_dict = {
            address: protocol_id
            for protocol_id, addresses in transferred_contracts_dict.items()
            for address in addresses
        }
        self.token_address_list = job_config.get("token_address")

    def get_filter(self):
        return TransactionFilterByLogs(
            [
                TopicSpecification(addresses=self.token_address_list),
                # maybe can add transfer topic here
            ]
        )

    def _get_current_holdings(self, block_number):
        session = self._service.get_service_session()
        sql = f"""
            select * from (select *, row_number() over (partition by wallet_address, contract_address,token_address order by block_number desc) rn
                   from af_staked_transferred_balance_hist
                   where block_number < {block_number}) t where rn = 1
            """
        result = session.execute(text(sql))

        current_holdings = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

        for record in result:
            contract_address = bytes_to_hex_str(record.contract_address)
            wallet_address = bytes_to_hex_str(record.wallet_address)
            token_address = bytes_to_hex_str(record.token_address)
            current_holdings[contract_address][wallet_address][token_address] = record.block_cumulative_value
        session.close()

        return current_holdings

    @staticmethod
    def extract_current_status(records, current_status_domain, keys):
        results = []
        last_records = distinct_collections_by_group(collections=records, group_by=keys, max_key="block_number")
        for last_record in last_records:
            record = current_status_domain(**vars(last_record))
            results.append(record)
        return results

    def _process(self, **kwargs):
        current_holdings = self._get_current_holdings(kwargs["start_block"])

        token_transfers = self._data_buff[ERC20TokenTransfer.type()]
        token_transfers.sort(key=lambda x: [x.block_number, x.log_index])
        protocol_wallet_token_block_group = defaultdict(
            lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        )
        for token_transfer in token_transfers:
            from_address = token_transfer.from_address
            to_address = token_transfer.to_address
            token_address = token_transfer.token_address
            block_number = token_transfer.block_number
            if from_address in self.address_protocol_dict:
                protocol_wallet_token_block_group[from_address][to_address][token_address][block_number].append(
                    {"token_transfer": token_transfer, "c": -1}
                )
            if to_address in self.address_protocol_dict:
                protocol_wallet_token_block_group[to_address][from_address][token_address][block_number].append(
                    {"token_transfer": token_transfer, "c": 1}
                )

        staked_records = []

        for protocol_address, wallet_token_block_group in protocol_wallet_token_block_group.items():
            for wallet_address, token_block_group in wallet_token_block_group.items():
                for token_address, block_group in token_block_group.items():
                    for block_number, token_transfers_group in block_group.items():
                        block_transfer_value = 0
                        for tc in token_transfers_group:
                            tc_token_transfer_ = tc["token_transfer"]
                            block_transfer_value += tc_token_transfer_.value * tc["c"]

                        current_block_cumulative_value = current_holdings[protocol_address][wallet_address][
                            token_address
                        ]
                        current_block_cumulative_value += block_transfer_value

                        current_holdings[protocol_address][wallet_address][
                            token_address
                        ] = current_block_cumulative_value

                        transferred_staked_detail = AfStakedTransferredBalanceHistDomain(
                            protocol_id=self.address_protocol_dict[protocol_address],
                            contract_address=protocol_address,
                            wallet_address=wallet_address,
                            token_address=token_address,
                            block_transfer_value=block_transfer_value,
                            block_cumulative_value=current_block_cumulative_value,
                            block_number=block_number,
                            block_timestamp=tc_token_transfer_.block_timestamp,
                        )
                        self._collect_domain(transferred_staked_detail)

                        staked_records.append(transferred_staked_detail)

        current_status = self.extract_current_status(
            staked_records,
            AfStakedTransferredBalanceCurrentDomain,
            keys=["contract_address", "wallet_address", "token_address"],
        )

        self._collect_domains(current_status)
