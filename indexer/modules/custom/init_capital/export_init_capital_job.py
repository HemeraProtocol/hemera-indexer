import logging

# Dependency dataclass
from indexer.domain.block import Block
from indexer.domain.transaction import Transaction
from indexer.domain.log import Log

# Job
from indexer.jobs.base_job import FilterTransactionDataJob

# Custom dataclass
from indexer.modules.custom.init_capital.abi import (
    INIT_BORROW_EVENT,
    INIT_COLLATERALIZE_EVENT,
    INIT_CREATE_POSITION_EVENT,
    INIT_DECOLLATERALIZE_EVENT,
    INIT_REPAY_EVENT,
)
from indexer.modules.custom.init_capital.domains.init_capital_domains import (
    InitCapitalPositionCreateDomain,
    InitCapitalPositionHistoryDomain,
    InitCapitalPositionUpdateDomain,
    InitCapitalRecordDomain,
)
from indexer.modules.custom.init_capital.models.init_capital_models import InitCapitalPositionCurrent
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs

# Utility
from common.utils.format_utils import bytes_to_hex_str

logger = logging.getLogger(__name__)

MONEY_MARKET_HOOK = "0xf82cbcab75c1138a8f1f20179613e7c0c8337346"
MARGIN_TRADING_HOOK = "0x7fa704E73262e5A9f48382087F69C6Aba0408eAA"

INIT_CORE = "0x972BcB0284cca0152527c4f70f8F689852bCAFc5"
POS_MANAGER = "0x0e7401707CD08c03CDb53DAEF3295DDFb68BBa92"

POOL_WETH = "0x51AB74f8B03F0305d8dcE936B473AB587911AEC4"
POOL_WBTC = "0x9c9F28672C4A8Ad5fb2c9Aca6d8D68B02EAfd552"
POOL_WMNT = "0x44949636f778fAD2b139E665aee11a2dc84A2976"
POOL_USDC = "0x00A55649E597d463fD212fBE48a3B40f0E227d06"
POOL_USDT = "0xadA66a8722B5cdfe3bC504007A5d793e7100ad09"
POOL_METH = "0x5071c003bB45e49110a905c1915EbdD2383A89dF"
POOL_USDE = "0x3282437C436eE6AA9861a6A46ab0822d82581b1c"
POOL_USDY = "0xf084813F1be067d980a0171F067f084f27B3F63A"
POOL_FBTC = "0x592c91Ac727DA556Dc90ddf5630e1901eFcd0c92"
LOOP_POOL_FBTC = "0x233493E9DC68e548AC27E4933A600A3A4682c0c3"

"""
https://docs.init.capital/
"""


class InitCapitalJob(FilterTransactionDataJob):
    # Declare existing dataclass you may need for your job
    # The indexer will automatically run other jobs and prepare the dataclass
    dependency_types = [Log]

    # This is to declare output dataclass your job outputs
    # This is helpful if you write other job which depends on these dataclasses
    output_types = [InitCapitalRecordDomain]

    able_to_reorg = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_service = kwargs["config"].get("db_service")
        self._pool_token_map = {
            LOOP_POOL_FBTC: "0xC96dE26018A54D51c097160568752c4E3BD6C364",
            POOL_FBTC: "0xC96dE26018A54D51c097160568752c4E3BD6C364",
        }

    def get_filter(self):
        topic_filter_list = [
            TopicSpecification(
                addresses=[INIT_CORE],
                topics=[
                    INIT_DECOLLATERALIZE_EVENT.get_signature(),
                    INIT_COLLATERALIZE_EVENT.get_signature(),
                    INIT_BORROW_EVENT.get_signature(),
                    INIT_REPAY_EVENT.get_signature(),
                    INIT_CREATE_POSITION_EVENT.get_signature(),
                ],
            )
        ]

        return TransactionFilterByLogs(topic_filter_list)

    def _collect(self, **kwargs):
        # This is how you get your dependency dataclass indexer prepared for you
        # Note that filter will apply
        logs = self._data_buff[Log.type()]

        # Core logic of UDF

        # 1. Create new position
        new_positions = []
        existing_position_ids = []
        for log in logs:
            if log.topic0 == INIT_CREATE_POSITION_EVENT.get_signature():
                decode_data = self.decode_log(log)
                new_position = InitCapitalPositionCreateDomain(
                    position_id=log.topic2,
                    owner_address=log.topic1,
                    viewer_address=decode_data["viewer"],
                    mode=decode_data["mode"],
                    created_block_number=log.block_number,
                    created_block_timestamp=log.block_timestamp,
                    created_transaction_hash=log.transaction_hash,
                    created_log_index=log.log_index,
                    block_number=log.block_number,
                    block_timestamp=log.block_timestamp,
                    transaction_hash=log.transaction_hash,
                    log_index=log.log_index,
                )
                new_positions.append(new_position)
            elif log.topic0 in [
                INIT_DECOLLATERALIZE_EVENT.get_signature(),
                INIT_COLLATERALIZE_EVENT.get_signature(),
            ]:
                existing_position_ids.append(log.topic1)
            elif log.topic0 in [
                INIT_BORROW_EVENT.get_signature(),
                INIT_REPAY_EVENT.get_signature(),
            ]:
                existing_position_ids.append(log.topic2)

        existing_position_ids = list(set(existing_position_ids))

        # Fetch existing postition
        existing_positions = self.get_existing_positions(existing_position_ids)
        existing_position_map = {p.position_id: p for p in existing_positions}


        # split block into groups and positions

        grouped_logs = {}
        for log in logs:
            if log.topic0 == INIT_CREATE_POSITION_EVENT.get_signature():
                continue
            if log.block_number not in grouped_logs:
                grouped_logs[log.block_number] = {}

            position_id = None
            if log.topic0 in [
                INIT_DECOLLATERALIZE_EVENT.get_signature(),
                INIT_COLLATERALIZE_EVENT.get_signature(),
            ]:
                position_id = log.topic1
            elif log.topic0 in [
                INIT_BORROW_EVENT.get_signature(),
                INIT_REPAY_EVENT.get_signature(),
            ]:
                position_id = log.topic2

            if not position_id:
                continue

            if position_id not in grouped_logs[log.block_number]:
                grouped_logs[log.block_number][position_id] = []

            grouped_logs[log.block_number][position_id].append(log)

        position_history = []
        records = []
        sorted_block_numbers = list(grouped_logs.keys()).sort()
        for block_nubmer in sorted_block_numbers:
            for position_id in grouped_logs[block_nubmer]:
                existing_position = existing_position_map.get(position_id)

                for log in  grouped_logs[block_nubmer][position_id]:
                    decode_data = self.decode_log(log)
                    if log.topic0 == INIT_COLLATERALIZE_EVENT.get_signature():
                        records.append(
                            InitCapitalRecordDomain(
                                action_type=1,
                                position_id=position_id,
                                pool_address=log.topic2,
                                token_address=self._pool_token_map[log.topic2],
                                amount=decode_data["amt"],
                                address=existing_position.viewer_address,
                                block_number=log.block_number,
                                block_timestamp=log.block_timestamp,
                                transaction_hash=log.transaction_hash,
                                log_index=log.log_index,
                            )
                        )
                        existing_position.collateral_amount += decode_data["amt"]

                    elif log.topic0 == INIT_DECOLLATERALIZE_EVENT.get_signature():
                        records.append(
                            InitCapitalRecordDomain(
                                action_type=3,
                                position_id=position_id,
                                pool_address=log.topic2,
                                token_address=self._pool_token_map[log.topic2],
                                amount=decode_data["amt"],
                                address=log.topic3,
                                block_number=log.block_number,
                                block_timestamp=log.block_timestamp,
                                transaction_hash=log.transaction_hash,
                                log_index=log.log_index,
                            )
                        )
                        existing_position.collateral_amount -= decode_data["amt"]
                    
                    elif log.topic0 == INIT_BORROW_EVENT.get_signature():
                        records.append(
                            InitCapitalRecordDomain(
                                action_type=2,
                                position_id=position_id,
                                pool_address=log.topic1,
                                token_address=self._pool_token_map[log.topic1],
                                amount=decode_data["borrowAmt"],
                                share=decode_data["shares"],
                                address=log.topic3,
                                block_number=log.block_number,
                                block_timestamp=log.block_timestamp,
                                transaction_hash=log.transaction_hash,
                                log_index=log.log_index,
                            )
                        )
                        existing_position.collateral_amount -= decode_data["amt"]
                    
                    elif log.topic0 == INIT_REPAY_EVENT.get_signature():
                        records.append(
                            InitCapitalRecordDomain(
                                action_type=4,
                                position_id=position_id,
                                pool_address=log.topic1,
                                token_address=self._pool_token_map[log.topic1],
                                amount=decode_data["amtToRepay"],
                                share=decode_data["shares"],
                                address=log.topic3,
                                block_number=log.block_number,
                                block_timestamp=log.block_timestamp,
                                transaction_hash=log.transaction_hash,
                                log_index=log.log_index,
                            )
                        )
                        existing_position.collateral_amount -= decode_data["amt"]
                
                existing_position.block_number=log.block_number
                existing_position.block_timestamp=log.block_timestamp
                existing_position.transaction_hash=log.transaction_hash
                existing_position.log_index=log.log_index
                
                position_history.append(
                    InitCapitalPositionHistoryDomain(
                        position_id=position_id,
                        owner_address=existing_position.owner_address,
                        viewer_address=existing_position.viewer_address,
                        mode=existing_position.mode,

                        collateral_pool_address=existing_position.collateral_pool_address,
                        collateral_token_addres=existing_position.collateral_token_addres,
                        collateral_amount=existing_position.collateral_amount,

                        borrow_pool_address=existing_position.borrow_pool_address,
                        borrow_token_address=existing_position.borrow_token_address,
                        borrow_share=existing_position.borrow_share,
                        borrow_amount=existing_position.borrow_amount,

                        block_number=existing_position.block_number,
                        block_timestamp=existing_position.block_timestamp,
                        transaction_hash=existing_position.transaction_hash,
                        log_index=existing_position.log_index,
                    )
                )



        # This is one of the functions that convert dataclass into models and export
        # The other functions can be found in indexer/jobs/base_job.py
        self._collect_domains(position_history)
        self._collect_domains(records)

    def _process(self, **kwargs):
        pass

    def get_existing_positions(self, existing_position_ids):
        if not self.db_service:
            return []
        existing_positions = []


        addresses = [ad[2:] for ad in addresses if ad and ad.startswith("0x")]
        if not addresses:
            return {}
        with self.db_service.get_service_session() as session:
            result = session.query(InitCapitalPositionCurrent).filter(
                InitCapitalPositionCurrent.position_id.in_(existing_position_ids)
            ).all()


        for record in result:
            existing_positions.append(
                InitCapitalPositionUpdateDomain(
                    position_id=record.position_id,
                    owner_address=bytes_to_hex_str(record.owner_address),
                    viewer_address=bytes_to_hex_str(record.viewer_address),
                    mode=record.mode,
                    collateral_pool_address=bytes_to_hex_str(record.owner_address),
                    collateral_token_addres=bytes_to_hex_str(record.owner_address),
                    collateral_amount=record.collateral_amount,
                    borrow_pool_address=bytes_to_hex_str(record.owner_address),
                    borrow_token_address=bytes_to_hex_str(record.owner_address),
                    borrow_share=record.borrow_share,
                    borrow_amount=record.borrow_amount,
                )
            )


        return existing_positions
