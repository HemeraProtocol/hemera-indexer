from sqlalchemy import func

from enumeration.eth_type import EthDataType
from exporters.jdbc.schema.blocks import Blocks
from exporters.jdbc.schema.transactions import Transactions
from exporters.jdbc.schema.logs import Logs


class PostgreSQLModelConverter:

    def convert_item(self, data_type, data):

        if data_type == EthDataType.BLOCK:
            return self.convert_to_block(data)

        elif data_type == EthDataType.TRANSACTION:
            return self.convert_to_transaction(data)

        elif data_type == EthDataType.LOG:
            return self.convert_to_log(data)

        else:
            return None

    def convert_to_block(self, block):
        return Blocks(
            hash=bytes(block.hash, 'utf-8'),
            number=block.number,
            timestamp=func.to_timestamp(block.timestamp),
            parent_hash=bytes(block.parent_hash, 'utf-8'),
            nonce=bytes(block.nonce, 'utf-8'),
            gas_limit=block.gas_limit,
            gas_used=block.gas_used,
            base_fee_per_gas=block.base_fee_per_gas,
            difficulty=block.difficulty,
            size=block.size,
            miner=bytes(block.miner, 'utf-8'),
            sha3_uncles=bytes(block.sha3_uncles, 'utf-8'),
            transactions_root=bytes(block.transactions_root, 'utf-8'),
            transactions_count=block.transactions_count,
            state_root=bytes(block.state_root, 'utf-8'),
            receipts_root=bytes(block.receipts_root, 'utf-8'),
            extra_data=bytes(block.extra_data, 'utf-8'),
            withdrawals_root=bytes(block.withdrawals_root, 'utf-8')
        )

    def convert_to_transaction(self, transaction):
        return Transactions(
            hash=bytes(transaction.hash, 'utf-8'),
            transaction_index=transaction.transaction_index,
            from_address=bytes(transaction.from_address, 'utf-8'),
            to_address=bytes(transaction.to_address, 'utf-8'),
            value=transaction.value,
            transaction_type=transaction.transaction_type,
            input=bytes(transaction.input, 'utf-8'),
            nonce=transaction.nonce,
            block_hash=bytes(transaction.block_hash, 'utf-8'),
            block_number=transaction.block_number,
            block_timestamp=func.to_timestamp(transaction.block_timestamp),
            gas=transaction.gas,
            gas_price=transaction.gas_price,
            max_fee_per_gas=transaction.max_fee_per_gas,
            max_priority_fee_per_gas=transaction.max_priority_fee_per_gas,
            receipt_root=bytes(transaction.receipt_root, 'utf-8') if transaction.receipt_root else None,
            receipt_status=transaction.receipt_status,
            receipt_gas_used=transaction.receipt_gas_used,
            receipt_cumulative_gas_used=transaction.receipt_cumulative_gas_used,
            receipt_effective_gas_price=transaction.receipt_effective_gas_price,
            receipt_l1_fee=transaction.receipt_l1_fee,
            receipt_l1_fee_scalar=transaction.receipt_l1_fee_scalar,
            receipt_l1_gas_used=transaction.receipt_l1_gas_used,
            receipt_l1_gas_price=transaction.receipt_l1_gas_price,
            blob_versioned_hashes=[bytes(_, 'utf-8') for _ in transaction.blob_versioned_hashes] \
                if transaction.blob_versioned_hashes else None,
            receipt_contract_address=bytes(transaction.receipt_contract_address, 'utf-8') if transaction.receipt_contract_address else None,
            exist_error=transaction.exist_error,
            error=transaction.error,
            revert_reason=transaction.revert_reason
        )

    def convert_to_log(self, log):
        return Logs(
            log_index=log.log_index,
            address=bytes(log.address, 'utf-8'),
            data=bytes(log.data, 'utf-8'),
            topic0=bytes(log.topic0, 'utf-8'),
            topic1=bytes(log.topic1, 'utf-8') if log.topic1 else None,
            topic2=bytes(log.topic2, 'utf-8') if log.topic2 else None,
            topic3=bytes(log.topic3, 'utf-8') if log.topic3 else None,
            transaction_hash=bytes(log.transaction_hash, 'utf-8'),
            transaction_index=log.transaction_index,
            block_number=log.block_number,
            block_hash=bytes(log.block_hash, 'utf-8'),
            block_timestamp=func.to_timestamp(log.block_timestamp)
        )
