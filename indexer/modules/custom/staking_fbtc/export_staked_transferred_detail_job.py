import ast
import configparser
import logging
import os
from collections import defaultdict

from sqlalchemy import text

from indexer.domain.token_transfer import ERC20TokenTransfer
from indexer.executors.batch_work_executor import BatchWorkExecutor
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.custom import common_utils
from indexer.modules.custom.feature_type import FeatureType
from indexer.modules.custom.staking_fbtc.domain.feature_staked_fbtc_detail import (
    TransferredStakedDetail,
)
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

logger = logging.getLogger(__name__)
FEATURE_ID = FeatureType.TRANSFERRED_FBTC.value


class ExportTransferredFBTCDetailJob(FilterTransactionDataJob):
    dependency_types = [ERC20TokenTransfer]
    output_types = [TransferredStakedDetail]
    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._batch_work_executor = BatchWorkExecutor(
            kwargs["batch_size"],
            kwargs["max_workers"],
            job_name=self.__class__.__name__,
        )
        self._max_worker = kwargs["max_workers"]
        self._chain_id = common_utils.get_chain_id(self._web3)
        self._load_config("config.ini", self._chain_id)
        self._service = kwargs["config"].get("db_service")

    def _load_config(self, filename, chain_id):
        base_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_path, filename)
        config = configparser.ConfigParser()
        config.read(full_path)

        try:
            transferred_protocol_dict_str = config.get(str(chain_id), "TRANSFERRED_CONTRACTS_DICT")
            self._transferred_protocol_dict = ast.literal_eval(transferred_protocol_dict_str)
            # add woofi、circuit
            self._transferred_protocol_dict.update({'0x82fde5086784e348aed03eb7b19ded97652db7a8': 'woofi',
                                                    '0x5b27576159d201697feb73e7cbe5dafcfdc9b0dc': 'circuit'})

            self._staked_address_list = config.get(str(chain_id), "STAKED_BTC_ADDRESS").split(
                ',')  # remember to remove the last one

            self._fbtc_address = config.get(str(chain_id), "FBTC_ADDRESS")
            self._cmeth_address = config.get(str(chain_id), "CMETH_ADDRESS")

        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            raise ValueError(f"Missing required configuration in {filename}: {str(e)}")

    def get_filter(self):
        # add woofi
        wecmeth_address = '0x872b6ff825da431c941d12630754036278ad7049'
        # add circuit
        circuit_address = '0x59e641de941cc794cdf6152eda0ef51210373d95'
        filer_address = self._staked_address_list + [self._fbtc_address, self._cmeth_address, wecmeth_address,
                                                     circuit_address]
        # filer_address = [circuit_address]

        filer_address_list = list(set(filer_address))
        return TransactionFilterByLogs(
            [
                TopicSpecification(addresses=filer_address_list),
            ]
        )

    def _get_current_holdings(self, block_number):
        session = self._service.get_service_session()
        sql = f"""
            select * from (select *, row_number() over (partition by wallet_address, contract_address,token_address order by block_number desc) rn
                   from feature_staked_transfer_detail_records
                   where block_number < {block_number}) t where rn = 1
            """
        result = session.execute(text(sql))

        current_holdings = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

        for record in result:
            contract_address = '0x' + record.contract_address.hex()
            wallet_address = '0x' + record.wallet_address.hex()
            token_address = '0x' + record.token_address.hex()
            current_holdings[contract_address][wallet_address][token_address] = record.block_cumulative_value
        session.close()

        return current_holdings

    def _process(self, **kwargs):
        current_holdings = self._get_current_holdings(kwargs["start_block"])

        token_transfers = self._data_buff[ERC20TokenTransfer.type()]
        token_transfers.sort(key=lambda x: [x.block_number, x.log_index])
        protocol_wallet_token_block_group = defaultdict(
            lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
        for token_transfer in token_transfers:
            if token_transfer.from_address in self._transferred_protocol_dict:
                protocol_wallet_token_block_group[token_transfer.from_address][token_transfer.to_address][
                    token_transfer.token_address][token_transfer.block_number].append(
                    {'token_transfer': token_transfer, 'c': -1})
            if token_transfer.to_address in self._transferred_protocol_dict:
                protocol_wallet_token_block_group[token_transfer.to_address][token_transfer.from_address][
                    token_transfer.token_address][token_transfer.block_number].append(
                    {'token_transfer': token_transfer, 'c': 1})

        # staked_records = []

        for protocol_address, wallet_token_block_group in protocol_wallet_token_block_group.items():
            for wallet_address, token_block_group in wallet_token_block_group.items():
                for token_address, block_group in token_block_group.items():
                    for block_number, token_transfers_group in block_group.items():
                        block_transfer_value = 0
                        for tc in token_transfers_group:
                            tc_token_transfer_ = tc['token_transfer']
                            block_transfer_value += tc_token_transfer_.value * tc['c']

                        current_block_cumulative_value = current_holdings[protocol_address][wallet_address][
                            token_address]
                        current_block_cumulative_value += block_transfer_value

                        current_holdings[protocol_address][wallet_address][
                            token_address] = current_block_cumulative_value

                        transferred_staked_detail = TransferredStakedDetail(
                            protocol_id=self._transferred_protocol_dict[protocol_address],
                            contract_address=protocol_address,
                            wallet_address=wallet_address,
                            token_address=token_address,
                            block_transfer_value=block_transfer_value,
                            block_cumulative_value=current_block_cumulative_value,
                            block_number=block_number,
                            block_timestamp=tc_token_transfer_.block_timestamp
                        )
                        self._collect_domain(transferred_staked_detail)

                        # staked_records.append(transferred_staked_detail)
        # todo: add current status

        pass
