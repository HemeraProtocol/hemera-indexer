def bridge_postgresql_(table, data, fixing=False):
    if table == "blocks":
        return convert_to_block(data, fixing)

    elif table == "transactions":
        return convert_to_transaction(data, fixing)

    elif table == "logs":
        return convert_to_log(data, fixing)

    elif table == "traces":
        return convert_to_trace(data, fixing)

    elif table == "contract_internal_transactions":
        return convert_to_contract_internal_transactions(data, fixing)

    elif table == "contracts":
        return convert_to_contract(data, fixing)

    elif table == "address_coin_balances":
        return convert_to_coin_balance(data, fixing)

    elif table == "erc20_token_transfers":
        return convert_to_erc20_token_transfer(data, fixing)

    elif table == "erc20_token_holders":
        return convert_to_erc20_token_holder(data, fixing)

    elif table == "erc721_token_transfers":
        return convert_to_erc721_token_transfer(data, fixing)

    elif table == "erc721_token_holders":
        return convert_to_erc721_token_holder(data, fixing)

    elif table == "erc721_token_id_changes":
        return convert_to_erc721_token_id_change(data, fixing)

    elif table == "erc721_token_id_details":
        return convert_to_erc721_token_id_detail(data, fixing)

    elif table == "erc1155_token_transfers":
        return convert_to_erc1155_token_transfer(data, fixing)

    elif table == "erc1155_token_holders":
        return convert_to_erc1155_token_holder(data, fixing)

    elif table == "erc1155_token_id_details":
        return convert_to_erc1155_token_id_detail(data, fixing)

    elif table == "tokens":
        return convert_to_tokens(data, fixing)

    elif table == "address_token_balances":
        return convert_to_token_balance(data, fixing)

    elif table == "block_ts_mapper":
        return convert_to_block_ts_mapper(data)

    else:
        return None