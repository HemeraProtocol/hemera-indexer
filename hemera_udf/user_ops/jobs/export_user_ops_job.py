import json
from typing import cast

from eth_typing import ABIEvent, ABIFunction
from web3._utils.contracts import decode_transaction_data
from web3._utils.normalizers import BASE_RETURN_NORMALIZERS

from hemera.common.utils.abi_code_utils import decode_log
from hemera.indexer.domains.log import Log
from hemera.indexer.domains.transaction import Transaction
from hemera.indexer.jobs import FilterTransactionDataJob
from hemera.indexer.specification.specification import TopicSpecification, TransactionFilterByLogs
from hemera_udf.user_ops.domains import UserOperationsResult

CONTRACT_ADDRESS = "0x5ff137d4b0fdcd49dca30c7cf57e578a026d2789"
BEFOREEXECUTION_FUNCTION_SIGN = "0xbb47ee3e183a558b1a2ff0874b079f3fc5478b7454eacf2bfc5af2ff5878f972"
USEROPERATIONEVENT_FUNCTION_SIGN = "0x49628fd1471006c1482da88028e9ce4dbb080b815c9b0344d39e5a8e6ec1419f"

HANDLEOPS_EVENT = cast(
    ABIEvent,
    json.loads(
        """ { "inputs": [ { "components": [ { "internalType": "address", "name": "sender", "type": "address" }, { "internalType": "uint256", "name": "nonce", "type": "uint256" }, { "internalType": "bytes", "name": "initCode", "type": "bytes" }, { "internalType": "bytes", "name": "callData", "type": "bytes" }, { "internalType": "uint256", "name": "callGasLimit", "type": "uint256" }, { "internalType": "uint256", "name": "verificationGasLimit", "type": "uint256" }, { "internalType": "uint256", "name": "preVerificationGas", "type": "uint256" }, { "internalType": "uint256", "name": "maxFeePerGas", "type": "uint256" }, { "internalType": "uint256", "name": "maxPriorityFeePerGas", "type": "uint256" }, { "internalType": "bytes", "name": "paymasterAndData", "type": "bytes" }, { "internalType": "bytes", "name": "signature", "type": "bytes" } ], "internalType": "struct UserOperation[]", "name": "ops", "type": "tuple[]" }, { "internalType": "address payable", "name": "beneficiary", "type": "address" } ], "name": "handleOps", "outputs": [], "stateMutability": "nonpayable", "type": "function" }"""
    ),
)

USEROPERATIONEVENT_EVENT = cast(
    ABIEvent,
    json.loads(
        """ { "anonymous": false, "inputs": [ { "indexed": true, "internalType": "bytes32", "name": "userOpHash", "type": "bytes32" }, { "indexed": true, "internalType": "address", "name": "sender", "type": "address" }, { "indexed": true, "internalType": "address", "name": "paymaster", "type": "address" }, { "indexed": false, "internalType": "uint256", "name": "nonce", "type": "uint256" }, { "indexed": false, "internalType": "bool", "name": "success", "type": "bool" }, { "indexed": false, "internalType": "uint256", "name": "actualGasCost", "type": "uint256" }, { "indexed": false, "internalType": "uint256", "name": "actualGasUsed", "type": "uint256" } ], "name": "UserOperationEvent", "type": "event" }"""
    ),
)


class ExportUserOpsJob(FilterTransactionDataJob):
    dependency_types = [Transaction, Log]
    output_types = [UserOperationsResult]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_filter(self):
        # return TransactionFilterByTransactionInfo(ToAddressSpecification(CONTRACT_ADDRESS))
        return TransactionFilterByLogs(
            [
                TopicSpecification(
                    addresses=[CONTRACT_ADDRESS],
                    topics=[USEROPERATIONEVENT_FUNCTION_SIGN],
                )
            ]
        )

    def _collect(self, **kwargs):
        pass

    def _process(self, **kwargs):
        transactions = list(filter(self.get_filter().is_satisfied_by, self._data_buff[Transaction.type()]))
        if transactions:
            logs = self._data_buff.get("log")
            for transaction in transactions:
                _logs = [log for log in logs if log.transaction_hash == transaction.hash]
                user_operation_result_list = self._export_results_from_transaction(transaction, _logs)
                for user_operation_result in user_operation_result_list:
                    self._collect_item(UserOperationsResult.type(), user_operation_result)

    @staticmethod
    def _export_results_from_transaction(transaction, logs):
        transaction_input = decode_transaction_data(
            cast(ABIFunction, HANDLEOPS_EVENT),
            transaction.input,
            normalizers=BASE_RETURN_NORMALIZERS,
        )

        user_operations = transaction_input["ops"]
        user_operations_count = user_operations.__len__()

        logs_index_list = []  # todo: check if beforeExecution

        user_operation_event_logs = []
        for log in logs:
            function_sign = log.topic0
            if function_sign == BEFOREEXECUTION_FUNCTION_SIGN:
                if logs_index_list:
                    # raise 'before execution has something problem'
                    return []
                else:
                    logs_index_list.append(log.log_index)

            if log.address == CONTRACT_ADDRESS and function_sign == USEROPERATIONEVENT_FUNCTION_SIGN:
                user_operation_event_logs.append(log)
                logs_index_list.append(log.log_index)

        user_operation_event_logs_count = user_operation_event_logs.__len__()

        if user_operations_count != user_operation_event_logs_count:
            return []
            # raise Exception('the count NOT meet')

        user_operation_result_list = []
        logs_index_pair = [(logs_index_list[i], logs_index_list[i + 1]) for i in range(len(logs_index_list) - 1)]
        for user_operation, user_operation_event_log, logs_index in zip(
            user_operations, user_operation_event_logs, logs_index_pair
        ):

            user_operation_event_log_decode_data = decode_log(USEROPERATIONEVENT_EVENT, user_operation_event_log)

            if not (
                user_operation["sender"].lower() == user_operation_event_log_decode_data["sender"]
                and user_operation["nonce"] == user_operation_event_log_decode_data["nonce"]
            ):
                return []

            user_operations_result = UserOperationsResult(
                user_op_hash=user_operation_event_log_decode_data["userOpHash"],
                sender=user_operation_event_log_decode_data["sender"],
                paymaster=user_operation_event_log_decode_data["paymaster"],
                nonce=user_operation_event_log_decode_data["nonce"],
                status=user_operation_event_log_decode_data["success"],
                actual_gas_cost=user_operation_event_log_decode_data["actualGasCost"],
                actual_gas_used=user_operation_event_log_decode_data["actualGasUsed"],
                init_code=user_operation["initCode"],
                call_data=user_operation["callData"],
                call_gas_limit=user_operation["callGasLimit"],
                verification_gas_limit=user_operation["verificationGasLimit"],
                pre_verification_gas=user_operation["preVerificationGas"],
                max_fee_per_gas=user_operation["maxFeePerGas"],
                max_priority_fee_per_gas=user_operation["maxPriorityFeePerGas"],
                paymaster_and_data=user_operation["paymasterAndData"],
                signature=user_operation["signature"],
                transactions_hash=transaction.hash,
                transactions_index=transaction.transaction_index,
                block_number=transaction.block_number,
                block_timestamp=transaction.block_timestamp,
                bundler=transaction.from_address,
                start_log_index=logs_index[0],
                end_log_index=logs_index[1],
            )
            user_operation_result_list.append(user_operations_result)
        return user_operation_result_list
