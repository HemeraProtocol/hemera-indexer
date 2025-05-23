from __future__ import annotations

import codecs

from eth_abi import encoding
from eth_abi.decoding import StringDecoder
from eth_abi.registry import BaseEquals, registry


class CompatibleStringDecoder(StringDecoder):

    @staticmethod
    def decoder_fn(data, handle_string_errors="strict"):
        try:
            return data.decode("utf-8", errors=handle_string_errors)
        except UnicodeDecodeError:
            try:
                return data.decode("latin-1", errors=handle_string_errors)
            except UnicodeDecodeError:
                return codecs.decode(data, "hex")


lifo_registry = registry.copy()
lifo_registry.unregister("string")

lifo_registry.register(
    BaseEquals("string"),
    encoding.TextStringEncoder,
    CompatibleStringDecoder,
    label="string",
)
