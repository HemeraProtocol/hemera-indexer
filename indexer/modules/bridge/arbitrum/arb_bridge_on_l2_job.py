from enumeration.entity_type import EntityType
from indexer.domain.transaction import Transaction
from indexer.jobs import FilterTransactionDataJob
from indexer.modules.bridge.arbitrum.arb_parser import *
from indexer.modules.bridge.domain.arbitrum import ArbitrumL1ToL2TransactionOnL2, ArbitrumL2ToL1TransactionOnL2
from indexer.specification.specification import TopicSpecification, TransactionFilterByLogs


class ArbitrumBridgeOnL2Job(FilterTransactionDataJob):
    dependency_types = [Transaction]
    output_types = [ArbitrumL1ToL2TransactionOnL2, ArbitrumL2ToL1TransactionOnL2]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        config = kwargs["config"]

        self._contract_list = [address.lower() for address in set(config.get("contract_list"))]

    def get_filter(self):
        topics = []
        addresses = self._contract_list

        topics.append(TICKET_CREATED_EVENT_SIG)
        topics.append(L2ToL1Tx64_EVENT_SIG)
        topics.append(BEACON_UPGRADED_EVENT_SIG)
        topics.append(DEPOSIT_FINALIZED_EVENT_SIG)

        return TransactionFilterByLogs([TopicSpecification(addresses=addresses, topics=topics)])

    def _process(self, **kwargs):
        # filter out transactions that are not bridge related
        transactions = list(filter(self.get_filter().is_satisfied_by, self._data_buff[Transaction.type()]))
        result = []
        ticket_created = []
        for tnx in transactions:
            x_lis = parse_ticket_created_event(tnx, self._contract_list)
            for x in x_lis:
                adt = ArbitrumL1ToL2TransactionOnL2(
                    msg_hash=x.msg_hash,
                    l2_block_number=tnx.block_number,
                    l2_block_timestamp=tnx.block_timestamp,
                    l2_block_hash=str(tnx.block_hash),
                    l2_transaction_hash=str(tnx.hash),
                    l2_from_address=x.from_address,
                    l2_to_address=x.to_address,
                )
                ticket_created.append(adt)
        # l2 -> l1
        l2_to_l1 = []
        for tnx in transactions:
            x_lis = parse_l2_to_l1_tx_64_event(tnx, self._contract_list)
            for x in x_lis:
                l2_to_l1.append(
                    ArbitrumL2ToL1TransactionOnL2(
                        msg_hash=x.msg_hash,
                        index=x.position,
                        l2_block_number=x.l2_block_number,
                        l2_block_timestamp=x.l2_block_timestamp,
                        l2_block_hash=x.l2_block_hash,
                        l2_transaction_hash=x.l2_transaction_hash,
                        l2_from_address=x.l2_from_address,
                        l2_to_address=x.l2_to_address,
                        amount=x.callvalue,
                        from_address=x.caller,
                        to_address=x.destination,
                        l1_token_address=None,
                        l2_token_address=(strip_leading_zeros(x.l2_token_address) if x.l2_token_address else None),
                        extra_info={},
                    )
                )
        bridge_tokens = []
        for tnx in transactions:
            x = parse_bridge_token(tnx, self._contract_list)
            bridge_tokens.extend(x)
        result += ticket_created
        result += l2_to_l1
        result += bridge_tokens
        for data in result:
            self._collect_item(data.type(), data)
