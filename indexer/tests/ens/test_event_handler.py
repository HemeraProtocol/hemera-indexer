#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/8/27 15:18
# @Author  will
# @File  test_event_handler.py
# @Brief


def test_event_handler():
    ens_event = EnsEvent(ens_conf.contract_map)
    ens_event_handler = EnsEventHandler(ens_event)

    from web3 import Web3

    w3 = Web3(Web3.HTTPProvider(config.get("DEFAULT", "PROVIDER_URI")))
    tra = "0x7b73669a4ea477ebccd0850e4458f1f60958835f8bb97727e99fd8fc10e896d6"
    transaction = w3.eth.get_transaction(tra)
    block = w3.eth.get_block(transaction["blockNumber"])
    transaction = dict(transaction)
    transaction["blockTimestamp"] = block["timestamp"]
    transaction["from_address"] = transaction["from"].lower()
    transaction["to_address"] = transaction["to"].lower()
    transaction["hash"] = Web3.toHex(transaction["hash"])
    transaction["blockHash"] = Web3.toHex(transaction["blockHash"])

    recepits = w3.eth.get_transaction_receipt(tra)  # not yet mined
    logs = recepits["logs"]
    f_logs = []
    for ll in logs:
        tmp = dict(ll)
        tmp["topics"] = [Web3.toHex(ele) for ele in tmp["topics"]]
        f_logs.append(convert_keys_to_snake_case(tmp))
    res = ens_event_handler.process(convert_keys_to_snake_case(transaction), f_logs)
    print(res)
    ens_transfer_insert_stmt = create_insert_statement_for_table(ENS_Middle)

    item_exporter = PostgresItemExporter(
        config.get("DEFAULT", "ENS_PG_URI"), item_type_to_insert_stmt_mapping={"ens_middle": ens_transfer_insert_stmt}
    )
    item_exporter.export_items_with_session(res)
