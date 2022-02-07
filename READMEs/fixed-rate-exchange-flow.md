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

To get started with this guide, please refer to [datatokens-flow](datatokens-flow.md) and complete the following steps :
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library from v4 sources

### Set envvars

Set the required enviroment variables as described in [datatokens-flow](datatokens-flow.md):
- [x] Setup : Set envvars

## 2. Alice publishes Data NFT & Datatoken

In your project folder (i.e. my_project from `Install the library` step) and in the work console where you set envvars, run the following:

Please refer to [datatokens-flow](datatokens-flow.md) and complete the following steps :
- [x] 2.1 Create an ERC721 data NFT
- [x] 2.2 Create an erc20 datatoken from the data NFT

## 3. Alice mints datatokens

In the same python console:
```python
#Mint the datatokens
erc20_token.mint(alice_wallet.address, ocean.to_wei(100), alice_wallet)
```

## 4. Bob buys at fixed rate datatokens

In the same python console:
```python
bob_private_key = os.getenv('TEST_PRIVATE_KEY2')
bob_wallet = Wallet(ocean.web3, bob_private_key, config.block_confirmations, config.transaction_timeout)
print(f"bob_wallet.address = '{bob_wallet.address}'")

# Verify that Bob has ganache ETH
assert ocean.web3.eth.get_balance(bob_wallet.address) > 0, "need ganache ETH"

OCEAN_token = ocean.get_datatoken(ocean.OCEAN_address)
```

If the `exchange_id` is not provided yet, here is the fix.
It is important to create an `exchange_id` only one time per exchange.

```python
#Create exchange_id for a new exchange
exchange_id = ocean.create_fixed_rate(
    erc20_token=erc20_token,
    base_token=OCEAN_token,
    amount=ocean.to_wei(100),
    from_wallet=alice_wallet,
)
```

If `exchange_id` has been created before or there are other
exchanges for a certain datatoken, it can be searched by
providing the datatoken address.

```python
# Search for exchange_id from a specific block retrieved at 3rd step
# for a certain datatoken address (e.g. datatoken_address). Choose
# one from the list.
datatoken_address = erc20_token.address
nft_factory = ocean.get_nft_factory()
logs = nft_factory.search_exchange_by_datatoken(ocean.fixed_rate_exchange, datatoken_address)
# Optional: Filtering the logs by the exchange owner.
logs = nft_factory.search_exchange_by_datatoken(ocean.fixed_rate_exchange, datatoken_address, alice_wallet.address)
print(logs)
```

Use the `exchange_id` for buying at fixed rate.

```python
# Approve tokens for Bob
fixed_price_address = ocean.fixed_rate_exchange.address
erc20_token.approve(fixed_price_address, ocean.to_wei(100), bob_wallet)
OCEAN_token.approve(fixed_price_address, ocean.to_wei(100), bob_wallet)

tx_result = ocean.fixed_rate_exchange.buy_dt(
    exchange_id=exchange_id,
    datatoken_amount=ocean.to_wei(20),
    max_base_token_amount=ocean.to_wei(50),
    from_wallet=bob_wallet,
    )
assert tx_result, "failed buying datatokens at fixed rate for Bob"
```

As an alternative to publishing the nft, the datatoken and the fixed rate exchange using separate transactions,
you can use the `create_nft_erc_fre_in_one_call` function to deploy them within a single
transaction. ocean.py also offers the option of creating the NFT, the ERC20 and a pool, exchange or
dispenser within the same transaction, using the PoolData, FixedData or DispenserData
as arguments.

```python
from ocean_lib.models.models_structures import CreateErc20Data, CreateERC721DataNoDeployer, FixedData
from ocean_lib.web3_internal.constants import ZERO_ADDRESS

nft_factory = ocean.get_nft_factory()
fixed_rate_address = ocean.fixed_rate_exchange.address

cap = ocean.to_wei(10)
erc721_data = CreateERC721DataNoDeployer(
    name="NFT",
    symbol="NFTSYMBOL",
    template_index=1,  # default value
    token_uri="https://oceanprotocol.com/nft/",
)
erc20_data = CreateErc20Data(
    template_index=1, # default value
    strings=["ERC20DT1", "ERC20DT1Symbol"], # name & symbol for ERC20 token
    addresses=[
        alice_wallet.address, # minter address
        alice_wallet.address, # fee manager for this ERC20 token
        alice_wallet.address, # publishing Market Address
        ZERO_ADDRESS, # publishing Market Fee Token
    ],
    uints=[cap, 0],
    bytess=[b""]
)
fixed_rate_data = FixedData(
    fixed_price_address=fixed_rate_address,
    addresses=[
        ocean.OCEAN_address,  # basetoken address
        alice_wallet.address,  # owner address
        bob_wallet.address,  # market fee collector address
        ZERO_ADDRESS,
    ],
    uints=[18, 18, ocean.to_wei("1"), ocean.to_wei("0.001"), 0],
    # basetoken decimals, datatoken decimals, fixed rate, market fee, with mint
)
erc721_token, erc20_token, exchange_id = nft_factory.create_nft_erc_fre_in_one_call(
    erc721_data=erc721_data,
    erc20_data=erc20_data,
    fixed_rate_data=fixed_rate_data,
    from_wallet=alice_wallet,
)
print(f"Created ERC721 token: done. Its address is {erc721_token.address}")
print(f"data NFT token name: {erc721_token.token_name()}")
print(f"data NFT token symbol: {erc721_token.symbol()}")

print(f"Created ERC20 datatoken: done. Its address is {erc20_token.address}")
print(f"datatoken name: {erc20_token.token_name()}")
print(f"datatoken symbol: {erc20_token.symbol()}")

print(f"Created Fixed Rate Exchange: done. Its exchange id is {exchange_id}")
```
