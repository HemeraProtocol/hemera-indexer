from common.models.contracts import Contracts


def format_contract_data(contract_dict):
    contract = contract_dict
    contract['model'] = Contracts

    return contract


def extract_contract_from_trace(trace):
    contract = {
        'address': trace['to_address'],
        'contract_creator': trace['from_address'],
        'creation_code': trace['input'],
        'deployed_code': trace['output'],
        'block_number': trace['block_number'],
        'transaction_index': trace['transaction_index'],
        'transaction_hash': trace['transaction_hash'],
    }

    return contract
