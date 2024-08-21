import logging
from typing import Any, Callable, Iterable, List, Optional, Tuple, Union

import orjson
from eth_typing import Address, ChecksumAddress, HexAddress
from eth_typing.abi import Decodable
from eth_utils import to_checksum_address

from indexer.utils.multicall_hemera.signature import Signature, _get_signature

logger = logging.getLogger(__name__)

AnyAddress = Union[str, Address, ChecksumAddress, HexAddress]


class Call:

    def __init__(
        self,
        target: AnyAddress,
        function: Union[str, Iterable[Union[str, Any]]],
        returns: Optional[Iterable[Tuple[str, Callable]]] = None,
        block_id: Optional[int] = None,
        gas_limit: Optional[int] = None,
    ) -> None:
        self.target = to_checksum_address(target)
        self.returns = returns
        self.block_id = block_id
        self.gas_limit = gas_limit

        self.args: Optional[List[Any]]
        if isinstance(function, list):
            self.function, *self.args = function
        else:
            self.function = function
            self.args = None
        self.signature = _get_signature(self.function)

    def __repr__(self) -> str:
        return f"<Call {self.function} on {self.target[:8]}>"

    @property
    def data(self) -> bytes:
        return self.signature.encode_data(self.args)

    def decode_output(
        output: Decodable,
        signature: Signature,
        returns: Optional[Iterable[Tuple[str, Callable]]] = None,
        success: Optional[bool] = None,
    ) -> Any:

        if success is None:
            apply_handler = lambda handler, value: handler(value)
        else:
            apply_handler = lambda handler, value: handler(success, value)

        if success is None or success:
            try:
                decoded = signature.decode_data(output)
            except:
                success, decoded = False, [None] * (1 if not returns else len(returns))  # type: ignore
        else:
            decoded = [None] * (1 if not returns else len(returns))  # type: ignore

        logger.debug(f"returns: {returns}")
        logger.debug(f"decoded: {decoded}")

        if returns:
            return {
                name: apply_handler(handler, value) if handler else value
                for (name, handler), value in zip(returns, decoded)
            }
        else:
            return decoded if len(decoded) > 1 else decoded[0]

    def to_rpc_param(self):
        args = prep_args(self.target, self.signature, self.args, self.block_id, self.gas_limit)
        args[0]["data"] = "0x" + (args[0]["data"]).hex()
        return {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": args,
            "id": hash(orjson.dumps(args)),
        }


def prep_args(target: str, signature: Signature, args: Optional[Any], block_id: Optional[int], gas_limit: int) -> List:
    call_data = signature.encode_data(args)

    args = [{"to": target, "data": call_data}, hex(block_id)]

    if gas_limit:
        args[0]["gas"] = gas_limit

    return args
