<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Consume Flow

This quickstart describes how data is consumed / downloaded, including metadata.

It focuses on Alice's experience as a publisher, and Bob's experience as a consumer.

Here are the steps:

1.  Setup
2.  Alice publishes data asset
3.  Bob downloads it

Let's go through each step.

## 1. Setup

### First steps

To get started with this guide, please refer to [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md) and complete the following steps :
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library from v4 sources
- [x] Setup : Set envvars

## 2. Publish Data NFT & Datatoken

In your project folder (i.e. my_project from `Install the library` step) and in the work console where you set envvars, run the following:

Please refer to [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md) and complete the following steps :
- [x] 2.1 Create a data NFT

Then, please refer to [publish-flow](publish-flow.md) and complete the following steps :
- [x] 2. Publish Dataset

## 3. Bob downloads the dataset
Now, you're Bob the data consumer.
In usual cases, Bob buys the dataset but here, let's have Alice send him some tokens directly.

Needed to mint fake OCEAN for testing with ganache:

`export FACTORY_DEPLOYER_PRIVATE_KEY=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58`

Then, in the same console:

```python
# Bob's wallet
bob_private_key = os.getenv('TEST_PRIVATE_KEY2')
bob_wallet = Wallet(ocean.web3, bob_private_key, config.block_confirmations, config.transaction_timeout)
print(f"bob_wallet.address = '{bob_wallet.address}'")

# Verify that Bob has ganache ETH
assert ocean.web3.eth.get_balance(bob_wallet.address) > 0, "need ganache ETH"

# Verify that Bob has ganache OCEAN
OCEAN_token = ocean.OCEAN_token
assert OCEAN_token.balanceOf(bob_wallet.address) > 0, "need ganache OCEAN"

# Mint 1 datatoken in consumer wallet from publisher
datatoken = ocean.get_datatoken(asset.datatokens[0]["address"])
datatoken.mint(
    account_address=bob_wallet.address,
    value=ocean.to_wei("1"),
    from_wallet=alice_wallet,
)

# Bob points to the service object
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
fee_receiver = ZERO_ADDRESS  # could also be market address
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

# Bob downloads. If the connection breaks, Bob can request again by showing order_tx_id.
file_path = ocean.assets.download_asset(
    asset=asset,
    service=service,
    consumer_wallet=bob_wallet,
    destination='./',
    order_tx_id=order_tx_id
)
print(f"file_path = '{file_path}'")  # e.g. datafile.0xAf07...
```

In console:

```console
# verify that the file is downloaded
cd my_project/datafile.did:op:0xAf07...
ls branin.arff
```

Congrats to Bob for buying and consuming a data asset!

_Note_. The file is in ARFF format, used by some AI/ML tools. In this case there are two input variables (x0, x1) and one output.

```console
% 1. Title: Branin Function
% 3. Number of instances: 225
% 6. Number of attributes: 2

@relation branin

@attribute 'x0' numeric
@attribute 'x1' numeric
@attribute 'y' numeric

@data
-5.0000,0.0000,308.1291
-3.9286,0.0000,206.1783
...
```

Note on asset encryption: In order to encrypt the entire asset, when using a private market or metadata cache, use the encrypt keyword.
Same for compression and you can use a combination of the two. E.g:
`asset = ocean.assets.create(..., encrypt_flag=True)` or `asset = ocean.assets.create(..., compress_flag=True)`
