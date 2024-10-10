from typing import List

from eth_utils import to_checksum_address
from web3 import Web3

from indexer.domain.transaction import Transaction


class Specification:
    def is_satisfied_by(self, item):
        raise NotImplementedError("Must override is_satisfied_by")

    def __and__(self, other):
        return AndSpecification(self, other)

    def __or__(self, other):
        return OrSpecification(self, other)

    def __not__(self):
        return NotSpecification(self)


class AlwaysTrueSpecification(Specification):
    def is_satisfied_by(self, item):
        return True


class AlwaysFalseSpecification(Specification):
    def is_satisfied_by(self, item):
        return False


class AndSpecification(Specification):
    def __init__(self, *specifications):
        self.specifications = specifications

    def is_satisfied_by(self, item):
        return all(spec.is_satisfied_by(item) for spec in self.specifications)


class OrSpecification(Specification):
    def __init__(self, *specifications):
        self.specifications = specifications

    def is_satisfied_by(self, item):
        return any(spec.is_satisfied_by(item) for spec in self.specifications)


class NotSpecification(Specification):
    def __init__(self, specification):
        self.specification = specification

    def is_satisfied_by(self, item):
        return not self.specification.is_satisfied_by(item)


class FromAddressSpecification(Specification):
    def __init__(self, address):
        self.address = address

    def is_satisfied_by(self, item: Transaction):
        return item.from_address == self.address


class ToAddressSpecification(Specification):
    def __init__(self, address):
        self.address = address

    def is_satisfied_by(self, item: Transaction):
        return item.to_address == self.address


class FuncSignSpecification(Specification):
    def __init__(self, func_sign):
        assert func_sign.startswith("0x")
        assert len(func_sign) == 10
        self.func_sign = func_sign

    def is_satisfied_by(self, item: Transaction):
        return item.input[:10] == self.func_sign


class TopicSpecification(Specification):
    def __init__(self, topics: List[str] = [], addresses: List[str] = []):
        self.topics = topics
        self.addresses = addresses

    def is_satisfied_by(self, item: Transaction):
        if item.receipt is not None and item.receipt.logs is not None:
            for log in item.receipt.logs:
                if (len(self.topics) == 0 or log.topic0 in self.topics) and (
                    len(self.addresses) == 0 or log.address in self.addresses
                ):
                    return True
        return False

    def to_filter_params(self):
        params = {}
        if self.topics:
            params["topics"] = [self.topics]
        if self.addresses:
            params["address"] = [Web3.to_checksum_address(address) for address in self.addresses]
        return params


class TransactionHashSpecification(Specification):
    def __init__(self, hashes: List[str]):
        self.hashes = hashes

    def is_satisfied_by(self, item: Transaction):
        return item.hash in self.hashes


class TransactionFilterByLogs:
    def __init__(self, topics_filters: List[TopicSpecification]):
        self.specifications = topics_filters
        self.eth_log_filters_params = {
            "topics": [list(set([topic for spec in self.specifications for topic in spec.topics]))],
        }
        filter_addresses = [to_checksum_address(address) for spec in self.specifications for address in spec.addresses]
        if len(filter_addresses) > 0:
            self.eth_log_filters_params["address"] = filter_addresses

    def get_eth_log_filters_params(self):
        return [spec.to_filter_params() for spec in self.specifications]

    def is_satisfied_by(self, item: Transaction):
        return any(spec.is_satisfied_by(item) for spec in self.specifications)


class TransactionFilterByTransactionInfo:
    def __init__(self, *specifications):
        self.specifications = specifications

    def get_or_specification(self):
        return OrSpecification(*self.specifications)

    def is_satisfied_by(self, item: Transaction):
        return all(spec.is_satisfied_by(item) for spec in self.specifications)
