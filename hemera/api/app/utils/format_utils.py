import copy


def format_transaction(GAS_FEE_TOKEN_PRICE, transaction: dict):
    transaction_json = copy.copy(transaction)
    transaction_json["gas_fee_token_price"] = "{0:.2f}".format(GAS_FEE_TOKEN_PRICE)

    transaction_json["value"] = format_coin_value(int(transaction["value"]))
    transaction_json["value_dollar"] = "{0:.2f}".format(transaction["value"] * GAS_FEE_TOKEN_PRICE / 10**18)

    gas_price = transaction["gas_price"] or 0
    transaction_json["gas_price_gwei"] = "{0:.6f}".format(gas_price / 10**9).rstrip("0").rstrip(".")
    transaction_json["gas_price"] = "{0:.15f}".format(gas_price / 10**18).rstrip("0").rstrip(".")

    transaction_fee = gas_price * transaction["receipt_gas_used"]
    total_transaction_fee = gas_price * transaction["receipt_gas_used"]

    if "receipt_l1_fee" in transaction_json and transaction_json["receipt_l1_fee"]:
        transaction_json["receipt_l1_fee"] = (
            "{0:.15f}".format(transaction["receipt_l1_fee"] or 0 / 10**18).rstrip("0").rstrip(".")
        )
        transaction_json["receipt_l1_gas_price"] = (
            "{0:.15f}".format(transaction["receipt_l1_gas_price"] or 0 / 10**18).rstrip("0").rstrip(".")
        )
        transaction_json["receipt_l1_gas_price_gwei"] = (
            "{0:.6f}".format(transaction["receipt_l1_gas_price"] or 0 / 10**9).rstrip("0").rstrip(".")
        )

        total_transaction_fee = transaction_fee + transaction["receipt_l1_fee"]
    transaction_json["transaction_fee"] = "{0:.15f}".format(transaction_fee / 10**18).rstrip("0").rstrip(".")
    transaction_json["transaction_fee_dollar"] = "{0:.2f}".format(
        gas_price * GAS_FEE_TOKEN_PRICE * transaction["receipt_gas_used"] / 10**18
    )

    transaction_json["total_transaction_fee"] = (
        "{0:.15f}".format(total_transaction_fee / 10**18).rstrip("0").rstrip(".")
    )
    transaction_json["total_transaction_fee_dollar"] = "{0:.2f}".format(
        total_transaction_fee * GAS_FEE_TOKEN_PRICE / 10**18
    )
    return transaction_json


def format_dollar_value(value: float) -> str:
    """ """
    if value > 1:
        return "{0:.2f}".format(value)
    return "{0:.6}".format(value)


def format_coin_value(value: int, decimal: int = 18) -> str:
    """
    Formats a given integer value into a string that represents a token value.
    Parameters:
        value (int): The value to be formatted

    Returns:
        str: The formatted token value as a string.
    """
    if value < 1000:
        return str(value)
    else:
        return "{0:.15f}".format(value / 10**18).rstrip("0").rstrip(".")


def format_coin_value_with_unit(value: int, native_token: str) -> str:
    """
    Formats a given integer value into a string that represents a token value with the appropriate unit.
    For values below 1000, it returns the value in WEI.
    For higher values, it converts the value to a floating-point representation in the native token unit,
    stripping unnecessary zeros.

    Parameters:
        value (int): The value to be formatted, typically representing a token amount in WEI.
        native_token (str):

    Returns:
        str: The formatted token value as a string with the appropriate unit.
    """
    if value < 1000:
        return str(value) + " WEI"
    else:
        return "{0:.15f}".format(value / 10**18).rstrip("0").rstrip(".") + " " + native_token
