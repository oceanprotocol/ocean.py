<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Marketplace Flow

This quickstart describes a batteries-included flow including using off-chain services for metadata (Aquarius).

For pool creation, it is used as base token, OCEAN token.
The base token can be changed into something else, such as USDC, DAI etc., but
it will require an extra fee.

It focuses on Alice's experience as a publisher, and Bob's experience as a buyer.

Here are the steps:

1.  Setup
2.  Alice publishes data asset
3.  Market displays the asset for sale
4.  Bob buys data asset

Let's go through each step.

## 1. Setup

### First steps

To get started with this guide, please refer to [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md) and complete the following steps :
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library from v4 sources

### Run Ocean Market service

In a new console:

```console
#install
git clone https://github.com/oceanprotocol/market.git
cd market
npm install

#run Ocean Market app
npm start
```

Check out the Ocean Market webapp at http://localhost:8000.

Ocean Market is a graphical interface to the backend smart contracts and Ocean services (Aquarius, Provider). The following steps will interface to the backend in a different fashion: using the command-line / console, and won't need Ocean Market. But it's good to understand there are multiple views.
### Set envvars

Set the required enviroment variables as described in [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md):
- [x] Setup : Set envvars

## 2. Publish Data NFT & Datatoken

In your project folder (i.e. my_project from `Install the library` step) and in the work console where you set envvars, run the following:

Please refer to [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md) and complete the following steps :
- [x] 2.1 Create a data NFT

Then, please refer to [publish-flow](publish-flow.md) and complete the following steps :
- [x] 2. Publish Dataset

## 3. Creation of datatoken liquidity pool

In the following steps we will create a pool from the created token, in order to allow another user
to order this access token.
```python

# Mint OCEAN
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
mint_fake_OCEAN(config)

datatoken = ocean.get_datatoken(asset.services[0].datatoken)
OCEAN_token = ocean.OCEAN_token

bpool = ocean.create_pool(
    datatoken=datatoken,
    base_token=OCEAN_token,
    rate=ocean.to_wei(1),
    base_token_amount=ocean.to_wei(2000),
    lp_swap_fee_amount=ocean.to_wei("0.01"),
    publish_market_swap_fee_amount=ocean.to_wei("0.01"),
    publish_market_swap_fee_collector=alice_wallet.address,
    from_wallet=alice_wallet
)
print(f"BPool address: {bpool.address}")
```

## 4. Marketplace displays asset for sale

Now, you're the Marketplace operator. Here's how to get info about the data asset.

In the same Python console as before:

```python
prices = bpool.get_amount_in_exact_out(
    OCEAN_token.address, datatoken.address, ocean.to_wei(1), ocean.to_wei("0.01")
)
price_in_OCEAN = prices[0]

from ocean_lib.web3_internal.currency import pretty_ether_and_wei
print(f"Price of 1 {datatoken.symbol()} is {pretty_ether_and_wei(price_in_OCEAN, 'OCEAN')}")
```

## 5. Bob buys data asset
Now, you're Bob the data buyer.

In the same Python console as before:

```python
# Bob's wallet
bob_private_key = os.getenv('TEST_PRIVATE_KEY2')
bob_wallet = Wallet(ocean.web3, bob_private_key, config.block_confirmations, config.transaction_timeout)
print(f"bob_wallet.address = '{bob_wallet.address}'")

# Verify that Bob has ganache ETH
assert ocean.web3.eth.get_balance(bob_wallet.address) > 0, "need ganache ETH"

# Verify that Bob has ganache OCEAN
assert OCEAN_token.balanceOf(bob_wallet.address) > 0, "need ganache OCEAN"

# Bob buys 1.0 datatokens - the amount needed to buy the dataset.
OCEAN_token.approve(bpool.address, ocean.to_wei("10000"), from_wallet=bob_wallet)

bpool.swap_exact_amount_out(
    token_in=OCEAN_token.address,
    token_out=datatoken.address,
    consume_market_swap_fee_address=ZERO_ADDRESS,
    max_amount_in=ocean.to_wei(10),
    token_amount_out=ocean.to_wei(1),
    max_price=ocean.to_wei(10),
    consume_market_swap_fee_amount=0,
    from_wallet=bob_wallet,
)
assert datatoken.balanceOf(bob_wallet.address) >= ocean.to_wei(
    1
), "Bob didn't get 1.0 datatokens"

# Bob points to the service object
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
fee_receiver = ZERO_ADDRESS  # could also be market address
asset = ocean.assets.resolve(did)
service = asset.services[0]

# Bob sends his datatoken to the service
order_tx_id = ocean.assets.pay_for_access_service(
    asset,
    service,
    consume_market_order_fee_address=bob_wallet.address,
    consume_market_order_fee_token=datatoken.address,
    consume_market_order_fee_amount=0,
    wallet=bob_wallet,
)
print(f"order_tx_id = '{order_tx_id}'")
```

Congrats! Bob can now use the order_tx_id to consume the data asset.
For more details on consuming assets, check the **[Consume flow](READMEs/consume-flow.md)

As an alternative for publishing a NFT, a datatoken and a pool at once, you can use `create_nft_erc20_with_pool`.
