from typing import Tuple

from py_ecc.bn128 import FQ, field_modulus, multiply

from common.utils.format_utils import bytes_to_hex_str

# keep consistent with on-chain parameters, https://github.com/Layr-Labs/eigenlayer-middleware/blob/7d49b5181b09198ed275783453aa082bb3766990/src/libraries/BN254.sol#L324
exponent = int("0xc19139cb84c680a6e14116da060561765e05aa45a1c72a34f082305b61f3f52", 16)


def parse_solc_G1(solc_G1: Tuple[int, int]):
    x, y = solc_G1
    return FQ(x), FQ(y)


def map_to_curve(x: bytes) -> tuple:
    x_int = int.from_bytes(x, byteorder="big") % field_modulus

    while True:
        beta, y = find_y_from_x(x_int)

        if beta == (y**2) % field_modulus:
            return (x_int, y)

        x_int = (x_int + 1) % field_modulus

    return (0, 0)


def find_y_from_x(x: int) -> tuple:
    # beta = (x^3 + b) % p
    b = 3
    beta = (x**3 + b) % field_modulus
    y = pow(beta, exponent, field_modulus)
    return (beta, y)


def sign_message(private_key, message):
    point_on_curve = map_to_curve(message)
    signature = multiply(parse_solc_G1(point_on_curve), private_key)
    signature_bytes = b"".join(int(x).to_bytes(32, "big") for x in signature)
    signed = bytes_to_hex_str(signature_bytes)
    return signed
