from abc import abstractmethod
from typing import Optional, List, Dict, Any

from extractor.types import Transaction, Base, dict_to_dataclass, dataclass_to_dict


class ContractExtractor(object):
    def __init__(self, contract_event_map):
        self.contract_event_map = contract_event_map
        self.contract_addresses = contract_event_map.keys()
        self.events = contract_event_map.values()

    def extract(self, transaction: dict[str, Any]) -> Optional[list[dict[str, Any]]]:
        """
        Extracts bridge-related information from a blockchain transaction dictionary.

        Parameters:
            transaction (Dict[str, Any]): The transaction data as a dictionary.

        Returns:
            Optional[List[Dict[str, Any]]]: A list of dictionaries containing extracted data
            related to blockchain bridge transactions, or None if no relevant data could be extracted.
        """

        tx = dict_to_dataclass(transaction, Transaction)

        data = self._extract(tx)
        if data is None:
            return None
        else:
            return [dataclass_to_dict(d) for d in data]

    @abstractmethod
    def _extract(self, transaction: Transaction) -> Optional[List[Base]]:
        """
        Extracts bridge-related information from a blockchain transaction.

        Parameters:
            transaction (Transaction): The transaction data.

        Returns:
            Optional[List[Base]]: A list of extracted data related to blockchain bridge transactions,
            or None if no relevant data could be extracted.
        """

        raise NotImplementedError
