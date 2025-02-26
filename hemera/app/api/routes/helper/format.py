#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/12/20 14:58
# @Author  ideal
# @File  format.py
# @Brief

import copy
from typing import Union


def format_dollar_value(value: float) -> str:
    """ """
    if value > 1:
        return "{0:.2f}".format(value)
    return "{0:.6}".format(value)


def format_coin_value(value: Union[int, None], decimal: int = 18) -> str:
    """
    Formats a given integer value into a string that represents a token value.
    Parameters:
        value (int): The value to be formatted

    Returns:
        str: The formatted token value as a string.
    """
    if value is None:
        return "0"
    if value < 1000:
        return str(value)
    else:
        return "{0:.15f}".format(value / 10**decimal).rstrip("0").rstrip(".")


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
