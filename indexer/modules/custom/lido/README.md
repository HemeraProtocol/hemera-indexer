# Lido Staking Contract Overview

## Core Functions

```solidity
function balanceOf(address _account) external view returns (uint256) {
    return getPooledEthByShares(_sharesOf(_account));
}

function getPooledEthByShares(uint256 _sharesAmount) public view returns (uint256) {
    return _sharesAmount
        .mul(_getTotalPooledEther())
        .div(_getTotalShares());
}
    
function _getTotalPooledEther() internal view returns (uint256) {
    return _getBufferedEther()
        .add(CL_BALANCE_POSITION.getStorageUint256())
        .add(_getTransientBalance());
}

function _getBufferedEther() internal view returns (uint256) {
    return BUFFERED_ETHER_POSITION.getStorageUint256();
}

function _getTransientBalance() internal view returns (uint256) {
    uint256 depositedValidators = DEPOSITED_VALIDATORS_POSITION.getStorageUint256();
    uint256 clValidators = CL_VALIDATORS_POSITION.getStorageUint256();
    // clValidators can never be less than deposited ones.
    assert(depositedValidators >= clValidators);
    return (depositedValidators - clValidators).mul(DEPOSIT_SIZE);
}
```

## Contract Events

### TOTAL_SHARES_POSITION Events
```solidity
event TransferShares(
    address indexed from,
    address indexed to,
    uint256 sharesAmount
);

event SharesBurnt(
    address indexed account,
    uint256 preRebaseTokenAmount,
    uint256 postRebaseTokenAmount,
    uint256 sharesAmount
);
```

### BUFFERED_ETHER_POSITION Events
```solidity
event Submitted(
    address indexed sender,
    uint256 amount,
    address referral
);

event ELRewardsReceived(
    uint256 amount
);

event WithdrawalsReceived(
    uint256 amount
);

event Unbuffered(
    uint256 amount
);

event ETHDistributed(
    uint256 indexed reportTimestamp,
    uint256 preCLBalance,
    uint256 postCLBalance,
    uint256 withdrawalsWithdrawn,
    uint256 executionLayerRewardsWithdrawn,
    uint256 postBufferedEther
);
```

### Validator Related Events

```solidity
// CL_BALANCE_POSITION Event
event CLValidatorsUpdated(
    uint256 indexed reportTimestamp,
    uint256 preCLValidators,
    uint256 postCLValidators
);

// DEPOSITED_VALIDATORS_POSITION Event
event DepositedValidatorsChanged(
    uint256 depositedValidators    // Number of newly deposited validators
);

// CL_VALIDATORS_POSITION Event
event CLValidatorsUpdated(
    uint256 indexed reportTimestamp,
    uint256 preCLValidators,      // Validator count before update
    uint256 postCLValidators      // Validator count after update
);
```
