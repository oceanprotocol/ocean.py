<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Using Datatoken Enterprise

This quickstart describes a batteries-included flow including using a new template of ERC20,
called Datatoken Enterprise.

For dispenser & FRE, it is used as base token, OCEAN token.
The base token can be changed into something else, such as USDC, DAI etc., but
it will require an extra fee.

It focuses on Alice's experience as a publisher, and Bob's experience as a buyer & consumer.

Here are the steps:

1. Setup
2. Alice creates a NFT
3. Dispenser flow
4. Fixed Rate Exchange flow

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


## 2. Alice creates a NFT
In your project folder (i.e. my_project from `Install the library` step) and in the work console where you set envvars, run the following:

Please refer to [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md) and complete the following steps :
- [x] 2.1 Create a data NFT

## 3. Dispenser Flow

In the Python console:
```python
from ocean_lib.web3_internal.constants import ZERO_ADDRESS

datatoken_enterprise_token = data_nft.create_datatoken(
    name="DT1Name",  # name for datatoken
    symbol="DT1Symbol",  # symbol for datatoken
    template_index=2,  # this is the value for Datatoken Enterprise token
    from_wallet=alice_wallet,
    datatoken_cap=ocean.to_wei(50)
)
print(f"Datatoken Enterprise address: {datatoken_enterprise_token.address}")

```
Then, please refer to [publish-flow](publish-flow.md) to generate your metadata and encrypted files.
Asset creation will be based on the deployment of Datatoken Enterprise token like this:

```python
asset = ocean.assets.create(
    metadata,
    alice_wallet,
    encrypted_files,
    deployed_datatokens=[datatoken_enterprise_token]
)
access_service = asset.services[0]

bob_private_key = os.getenv("TEST_PRIVATE_KEY2")
bob_wallet = Wallet(
    ocean.web3,
    bob_private_key,
    config.block_confirmations,
    config.transaction_timeout,
)

# Verify that Bob has ganache ETH
assert ocean.web3.eth.get_balance(bob_wallet.address) > 0, "need ganache ETH"

# Create & activate dispenser
dispenser = ocean.dispenser
tx = datatoken_enterprise_token.create_dispenser(
    dispenser_address=dispenser.address,
    allowed_swapper=ZERO_ADDRESS,
    max_balance=ocean.to_wei(50),
    with_mint=True,
    max_tokens=ocean.to_wei(50),
    from_wallet=alice_wallet,
)
assert tx, "Dispenser not created!"

OCEAN_token = ocean.OCEAN_token
consume_fee_amount = ocean.to_wei(2)
datatoken_enterprise_token.set_publishing_market_fee(
    publish_market_order_fee_address=bob_wallet.address,
    publish_market_order_fee_token=OCEAN_token.address,  # can be also USDC, DAI
    publish_market_order_fee_amount=consume_fee_amount,
    from_wallet=alice_wallet,
)

# Approve tokens
OCEAN_token.approve(
    spender=datatoken_enterprise_token.address,
    amount=consume_fee_amount,
    from_wallet=alice_wallet,
)

# Prepare data for order
# Retrieve provider fee
(
    provider_fee_address,
    provider_fee_token,
    provider_fee_amount,
    v,
    r,
    s,
    valid_until,
    provider_data,
) = ocean.retrieve_provider_fees(
    asset=asset,
    access_service=access_service,
    publisher_wallet=alice_wallet
)


initial_bob_balance = OCEAN_token.balanceOf(bob_wallet.address)

# Bob gets 1 DT from dispenser and then startsOrder, while burning that DT
datatoken_enterprise_token.buy_from_dispenser_and_order(
    consumer=bob_wallet.address,
    service_index=1,
    provider_fee_address=provider_fee_address,
    provider_fee_token=provider_fee_token,
    provider_fee_amount=provider_fee_amount,
    v=v,
    r=r,
    s=s,
    valid_until=valid_until,
    provider_data=provider_data,
    consume_market_order_fee_address=bob_wallet.address,
    consume_market_order_fee_token=datatoken_enterprise_token.address,
    consume_market_order_fee_amount=0,
    dispenser_address=dispenser.address,
    from_wallet=alice_wallet,
)
increased_balance = OCEAN_token.balanceOf(bob_wallet.address)
assert initial_bob_balance < increased_balance
```

## 3. Fixed Rate Exchange Flow

In the Python console:
```python
from ocean_lib.web3_internal.constants import ZERO_ADDRESS

datatoken_enterprise_token = data_nft.create_datatoken(
    name="DT1Name",  # name for datatoken
    symbol="DT1Symbol",  # symbol for datatoken
    template_index=2,  # this is the value for Datatoken Enterprise token
    from_wallet=alice_wallet,
    datatoken_cap=ocean.to_wei(50)
)
print(f"Datatoken Enterprise address: {datatoken_enterprise_token.address}")

```
Then, please refer to [publish-flow](publish-flow.md) to generate your metadata and encrypted files.
Asset creation will be based on the deployment of Datatoken Enterprise token like this:

```python
asset = ocean.assets.create(
    metadata,
    alice_wallet,
    encrypted_files,
    deployed_datatokens=[datatoken_enterprise_token]
)
access_service = asset.services[0]

bob_private_key = os.getenv("TEST_PRIVATE_KEY2")
bob_wallet = Wallet(
    ocean.web3,
    bob_private_key,
    config.block_confirmations,
    config.transaction_timeout,
)

# Verify that Bob has ganache ETH
assert ocean.web3.eth.get_balance(bob_wallet.address) > 0, "need ganache ETH"

# Bob buys 1 DT from the FRE and then startsOrder, while burning that DT
fixed_rate_exchange = ocean.fixed_rate_exchange
OCEAN_token = ocean.OCEAN_token

exchange_id = ocean.create_fixed_rate(
    datatoken=datatoken_enterprise_token,
    base_token=OCEAN_token,
    amount=ocean.to_wei(25),
    from_wallet=alice_wallet,
)

# Prepare data for order
# Retrieve provider fee
(
    provider_fee_address,
    provider_fee_token,
    provider_fee_amount,
    v,
    r,
    s,
    valid_until,
    provider_data,
) = ocean.retrieve_provider_fees(
    asset=asset,
    access_service=access_service,
    publisher_wallet=alice_wallet
)

datatoken_enterprise_token.mint(alice_wallet.address, ocean.to_wei(20), alice_wallet)

# Approve tokens
OCEAN_token.approve(
    spender=datatoken_enterprise_token.address,
    amount=ocean.to_wei(1000),
    from_wallet=alice_wallet,
)
# Approve consume market fee tokens before starting order.
datatoken_enterprise_token.approve(
    spender=datatoken_enterprise_token.address,
    amount=ocean.to_wei(1000),
    from_wallet=alice_wallet
)

# Transfer some Datatoken Enterprise tokens to Bob for buying from the FRE
datatoken_enterprise_token.transfer(bob_wallet.address, ocean.to_wei(15), alice_wallet)
OCEAN_token.approve(
    spender=datatoken_enterprise_token.address,
    amount=ocean.to_wei(1000),
    from_wallet=bob_wallet,
)

tx_id = datatoken_enterprise_token.buy_from_fre_and_order(
    consumer=bob_wallet.address,
    service_index=1,
    provider_fee_address=provider_fee_address,
    provider_fee_token=provider_fee_token,
    provider_fee_amount=provider_fee_amount,
    v=v,
    r=r,
    s=s,
    valid_until=valid_until,
    provider_data=provider_data,
    consume_market_order_fee_address=bob_wallet.address,
    consume_market_order_fee_token=datatoken_enterprise_token.address,
    consume_market_order_fee_amount=0,
    exchange_contract=fixed_rate_exchange.address,
    exchange_id=exchange_id,
    max_base_token_amount=ocean.to_wei(10),
    consume_market_swap_fee_amount=ocean.to_wei("0.001"),  # 1e15 => 0.1%
    consume_market_swap_fee_address=bob_wallet.address,
    from_wallet=alice_wallet,
)
tx_receipt = ocean.web3.eth.wait_for_transaction_receipt(tx_id)
assert tx_receipt.status == 1, "failed buying data tokens from FRE."
```
