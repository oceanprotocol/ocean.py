<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Fixed Rate Exchange Flow

This quickstart describes fixed rate exchange flow created with OCEAN base token.
The base token can be changed into something else, such as USDC, DAI etc., but
it will require an extra fee.

It focuses on Alice's experience as a publisher, and Bob's experience as a buyer & consumer.

Here are the steps:

1.  Setup
2.  Alice creates a datatoken
3.  Alice mints & approves datatokens
4.  Bob buys at fixed rate datatokens

Let's go through each step.

## 1. Setup

### First steps

To get started with this guide, please refer to [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md) and complete the following steps :
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library from v4 sources

### Set envvars

Set the required enviroment variables as described in [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md):
- [x] Setup : Set envvars

## 2. Alice publishes Data NFT & Datatoken

In your project folder (i.e. my_project from `Install the library` step) and in the work console where you set envvars, run the following:

Please refer to [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md) and complete the following steps :
- [x] 2.1 Create a data NFT
- [x] 2.2 Create a datatoken from the data NFT

## 3. Alice mints datatokens

In the same python console:
```python
# Mint the datatokens
datatoken.mint(alice_wallet.address, ocean.to_wei(100), alice_wallet)
```

## 4. Bob buys at fixed rate datatokens

In the same python console:
```python
bob_private_key = os.getenv('TEST_PRIVATE_KEY2')
bob_wallet = Wallet(ocean.web3, bob_private_key, config.block_confirmations, config.transaction_timeout)
print(f"bob_wallet.address = '{bob_wallet.address}'")

# Verify that Bob has ganache ETH
assert ocean.web3.eth.get_balance(bob_wallet.address) > 0, "need ganache ETH"

OCEAN_token = ocean.OCEAN_token
# Create exchange_id for a new exchange
exchange_id = ocean.create_fixed_rate(
    datatoken=datatoken,
    base_token=OCEAN_token,
    amount=ocean.to_wei(100),
    from_wallet=alice_wallet,
)
```

Use the `exchange_id` for buying at fixed rate.

```python
# Approve tokens for Bob
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
fixed_price_address = ocean.fixed_rate_exchange.address
datatoken.approve(fixed_price_address, ocean.to_wei(100), bob_wallet)
OCEAN_token.approve(fixed_price_address, ocean.to_wei(100), bob_wallet)

tx_result = ocean.fixed_rate_exchange.buy_dt(
    exchange_id=exchange_id,
    datatoken_amount=ocean.to_wei(20),
    max_base_token_amount=ocean.to_wei(50),
    consume_market_swap_fee_address=ZERO_ADDRESS,
    consume_market_swap_fee_amount=0,
    from_wallet=bob_wallet,
)
assert tx_result, "failed buying datatokens at fixed rate for Bob"
```

As an alternative for publishing a NFT, a datatoken and a fixed rate exchange at once, you can use `create_nft_erc20_with_fixed_rate`.

If you already created the `exchange_id`, then you can reuse it.
If an exchange has been created before or there are other
exchanges for a certain datatoken, it can be searched by
providing the datatoken address.
```python
# Get a list exchange addresses and ids with a given datatoken and exchange owner.
datatoken_address = datatoken.address
nft_factory = ocean.get_nft_factory()
exchange_addresses_and_ids = nft_factory.search_exchange_by_datatoken(ocean.fixed_rate_exchange, datatoken_address)
# Optional: Filtering by the exchange owner.
exchange_addresses_and_ids = nft_factory.search_exchange_by_datatoken(ocean.fixed_rate_exchange, datatoken_address, alice_wallet.address)
print(exchange_addresses_and_ids)
```

