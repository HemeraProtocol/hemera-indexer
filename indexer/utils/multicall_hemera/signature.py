from functools import lru_cache
from typing import Any, List, Optional, Tuple

from eth_abi import decode, encode
from eth_typing.abi import Decodable, TypeStr
from eth_utils import function_signature_to_4byte_selector
from hexbytes import HexBytes

from indexer.utils.abi import pad_address, uint256_to_bytes


def parse_signature(signature: str) -> Tuple[str, List[TypeStr], List[TypeStr]]:
    """
    Breaks 'func(address)(uint256)' into ['func', ['address'], ['uint256']]
    """
    parts: List[str] = []
    stack: List[str] = []
    start: int = 0
    for end, character in enumerate(signature):
        if character == "(":
            stack.append(character)
            if not parts:
                parts.append(signature[start:end])
                start = end
        if character == ")":
            stack.pop()
            if not stack:  # we are only interested in outermost groups
                parts.append(signature[start : end + 1])
                start = end + 1
    function = "".join(parts[:2])
    input_types = parse_typestring(parts[1])
    output_types = parse_typestring(parts[2])
    return function, input_types, output_types


def parse_typestring(typestring: str) -> Optional[List[TypeStr]]:
    if typestring == "()":
        return []
    parts = []
    part = ""
    inside_tuples = 0
    for character in typestring[1:-1]:
        if character == "(":
            inside_tuples += 1
        elif character == ")":
            inside_tuples -= 1
        elif character == "," and inside_tuples == 0:
            parts.append(part)
            part = ""
            continue
        part += character
    parts.append(part)
    return parts


@lru_cache(maxsize=None)
def _get_signature(signature: str) -> "Signature":
    return Signature(signature)


class Signature:
    __slots__ = "signature", "function", "input_types", "output_types"

    def __init__(self, signature: str) -> None:
        self.signature = signature
        self.function, self.input_types, self.output_types = parse_signature(signature)

    @property
    def fourbyte(self) -> bytes:
        return function_signature_to_4byte_selector(self.function)

    def encode_data(self, args: Optional[List[Any]] = None) -> bytes:
        if args is None:
            args = []

        if len(args) != len(self.input_types):
            raise ValueError(f"Expected {len(self.input_types)} arguments, got {len(args)}")

        if len(args) > 2:
            return self.fourbyte + encode(self.input_types, args)

        encoded = self.fourbyte

        for arg, arg_type in zip(args, self.input_types):
            if arg_type == "address":
                encoded += pad_address(arg)
            elif arg_type == "uint256":
                encoded += uint256_to_bytes(arg)
            else:
                # cannot handle, call encode directly
                return self.fourbyte + encode(self.input_types, args)

        return encoded

    def decode_data(self, output: Decodable) -> Any:
        return decode(self.output_types, output)
