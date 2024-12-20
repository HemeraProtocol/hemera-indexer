# README for Uniswap V3 Jobs

## Overview
This project contains three scripts designed to retrieve foundational data from Uniswap V3-based decentralized exchanges (DEX), including pool addresses, prices, position tokens, liquidity, and other key metrics.

## Data Retrieval Logic
1. Retrieve pool information using the configured factory address.
2. Extract price data and swap events from the pools.
3. Retrieve detailed information about position tokens, such as owner and liquidity.

## Script Descriptions

### 1. [uniswap_v3_pool_job.py](jobs%2Funiswap_v3_pool_job.py)
- **Functionality:**
  - Extracts basic pool information from the `create pool` events of the factory address.
  - Data retrieved includes:
    - Pool address
    - Token0 and Token1 addresses
    - Fee tier

### 2. [uniswap_v3_pool_price_job.py](jobs%2Funiswap_v3_pool_price_job.py)
- **Functionality:**
  - Extracts price changes and swap events from `swap` events.
  - If specific pools are configured, the script will not query additional pools via RPC; otherwise, it will fetch extra pools dynamically.
  - Data retrieved includes:
    - Price changes
    - Transaction-related details (tick, sqrtPriceX96, etc.)

### 3. [uniswap_v3_token_job.py](jobs%2Funiswap_v3_token_job.py)
- **Functionality:**
  - Manages and updates ERC721 position token data from Uniswap V3.
  - Data retrieved includes:
    - Token creation, transfer, and burn events
    - Detailed position token information:
      - Token ID
      - Owner address
      - Liquidity
      - Tick range (lower and upper bounds)
      - Associated pool information

## Data Validation
To ensure the completeness and accuracy of Uniswap V3 data, the following validation logic can be applied:
1. From the pool's creation block onwards, calculate token0 and token1 balances using the Uniswap V3 formula.(As of any time)
2. Compare the calculated values with the actual token0 and token1 balances held by the pool, ensuring:
   - **Balance Proximity:** The calculated values are very close to the actual balances.
   - **Balance Sufficiency:** The actual pool balance is greater than or equal to the calculated values (the excess represents accumulated fees, which are returned to users during withdrawals).

This validation ensures the retrieved data is both complete and accurate.

## Example Data
The following example uses pool `0x383DD7f649d692F7897d4dF06b781Cd1E2E19293` and shows daily data for the week following its creation (July 11, 2024, to July 18, 2024). The table records the last transaction for each day, up to midnight the following day.

[View Transaction Details](https://explorer.mantle.xyz/tx/0x101fbf877d8baea339b854975ebeb9f9358eab3560552eb19e5b8b7e8c94a135)

| Date       | token0_balance_from_pool | token0_balance_from_lp | token0_balance_diff | token1_balance_from_pool | token1_balance_from_lp  | token1_balance_diff |
|------------|--------------------------|------------------------|---------------------|--------------------------|-------------------------|---------------------|
| 2024-07-11 | 50.00062461              | 50.00062304            | 0.00000157          | 752.0826152593331        | 752.08261525933         | 0.00000000000307    |
| 2024-07-12 | 53.0221513               | 53.01459585            | 0.00755545          | 697.2309928913661        | 697.230992891364        | 0.00000000000205    |
| 2024-07-13 | 53.02169931              | 53.01414385            | 0.00755546          | 697.2391600997217        | 697.239139681698        | 0.00002041802372    |
| 2024-07-14 | 53.01145519              | 53.00389972            | 0.00755547          | 697.4242682008088        | 697.423785012533        | 0.00048318827578    |
| 2024-07-15 | 53.01009811              | 53.00254107            | 0.00755704          | 697.4488475441887        | 697.448275046998        | 0.00057249719066    |
| 2024-07-16 | 53.01009811              | 53.00254106            | 0.00755705          | 697.520757746266         | 697.5200952490752541    | 0.00066249719077    |
| 2024-07-17 | 53.00972938              | 53.00217232            | 0.00755706          | 697.5274210169474        | 697.5267418615795488    | 0.00067915536783    |
| 2024-07-18 | 53.08610746              | 53.07831259            | 0.00779487          | 696.1561304974942        | 696.1546068136567314    | 0.00152368383749    |
The above two conditions are met every day, so the data index is correct and complete.