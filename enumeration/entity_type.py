class EntityType:
    BLOCK = 'block'
    TRANSACTION = 'transaction'
    RECEIPT = 'receipt'
    LOG = 'log'
    TOKEN_TRANSFER = 'token_transfer'
    TRACE = 'trace'
    CONTRACT = 'contract'
    TOKEN = 'token'
    COIN_BALANCE = 'coin_balance'

    ALL_FOR_STREAMING = [BLOCK, TRANSACTION, LOG, TOKEN_TRANSFER, TRACE, CONTRACT, TOKEN, RECEIPT, COIN_BALANCE]
    ALL_FOR_INFURA = [BLOCK, TRANSACTION, LOG, TOKEN_TRANSFER]
