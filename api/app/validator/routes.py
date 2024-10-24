#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Time    : 2024/10/22 下午4:55
Author  : xuzh
Project : hemera_indexer
"""
from flask_restx import Resource
from sqlalchemy import and_

from api.app.db_service.blocks import get_blocks_by_condition
from api.app.db_service.transactions import get_transactions_by_condition
from api.app.validator import validator_namespace
from api.app.validator.parse import validate_block_builder
from common.models.blocks import Blocks
from common.models.transactions import Transactions
from common.utils.format_utils import hex_str_to_bytes


@validator_namespace.route("/v1/validator/block/<number_or_hash>")
class ValidateBlock(Resource):
    """
    Get block data with transactions by given block number or block hash.

    :param number_or_hash: The block number or block hash to use for searching from db.
    :type number_or_hash: str

    :return: A json containing the block data with transaction json list.Can be None if no block is found.
    :rtype: json
    """

    def get(self, number_or_hash):

        if number_or_hash.isnumeric():
            number = int(number_or_hash)
            condition = and_(Blocks.number == number, Blocks.reorg == False)
        else:
            condition = and_(Blocks.hash == hex_str_to_bytes(number_or_hash), Blocks.reorg == False)

        block = get_blocks_by_condition(filter_condition=condition,
                                        columns=['hash', 'number', 'timestamp', 'parent_hash', 'transactions_count',
                                                 'extra_data'])

        if block is None:
            return None, 200

        transactions = get_transactions_by_condition(filter_condition=Transactions.block_number == block[0].number,
                                                     columns=['hash', 'transaction_index', 'from_address', 'to_address',
                                                              'value', 'input'])

        block_json = validate_block_builder(block[0], transactions)

        return block_json, 200
