#!/usr/bin/python3
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from hemera.common.utils.config import get_config
from hemera.common.utils.db_utils import get_total_row_count

app_config = get_config()


def get_count_by_address(table, chain, wallet_address=None):
    if not wallet_address:
        return get_total_row_count(table)

    # Try to get count from redis
    # get_count(f"{chain}_{table}_{wallet_address}")


def solve_nested_components(json_object, sb):
    string = json_object.get("type")

    if json_object.get("components"):
        components = json_object.get("components")
        sb.append("(")

        for j in range(len(components)):
            json_object1 = components[j]
            if json_object1.get("components"):
                solve_nested_components(json_object1, sb)
            else:
                inner_type = json_object1.get("type")
                sb.append(inner_type)

            if j < len(components) - 1:
                sb.append(",")

        sb.append(")")
        while string.endswith("[]"):
            sb.append("[]")
            string = string[:-2]
    else:
        sb.append(string)


def is_l1_block_finalized(block_number, timestamp):
    return timestamp < datetime.utcnow() - timedelta(minutes=15)


def is_l2_challenge_period_pass(block_number, timestamp):
    return timestamp < datetime.utcnow() - timedelta(days=7) - timedelta(minutes=15)
