<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Marketplace Flow

This quickstart describes a batteries-included flow including using off-chain services for metadata (Aquarius) and consuming datasets (Provider).

It focuses on Alice's experience as a publisher, and Bob's experience as a consumer.

Here are the steps:

1.  Setup
2.  Alice publishes data asset
3.  Bob downloads it

Let's go through each step.

## 1. Setup

### First steps

To get started with this guide, please refer to [datatokens-flow](datatokens-flow.md) and complete the following steps :
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library from v4 sources
- [x] Setup : Set envvars

## 2. Publish Data NFT & Datatoken

In your project folder (i.e. my_project from `Install the library` step) and in the work console where you set envvars, run the following:

Please refer to [datatokens-flow](datatokens-flow.md) and complete the following steps :
- [x] 2.1 Create an ERC721 data NFT

Then in the same python console:
```python
from ocean_lib.web3_internal.constants import ZERO_ADDRESS

# Specify metadata and services, using the Branin test dataset
date_created = "2021-12-28T10:55:11Z"

metadata = {
    "created": date_created,
    "updated": date_created,
    "description": "Branin dataset",
    "name": "Branin dataset",
    "type": "dataset",
    "author": "Trent",
    "license": "CC0: PublicDomain",
}

# ocean.py offers multiple file types, but a simple url file should be enough for this example
from ocean_lib.structures.file_objects import UrlFile
url_file = UrlFile(
    url="https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"
)

# Encrypt file(s) using provider
encrypted_files = ocean.assets.encrypt_files([url_file])


# Publish asset with services on-chain.
# The download (access service) is automatically created, but you can explore other options as well
asset = ocean.assets.create(
    metadata,
    alice_wallet,
    encrypted_files,
    erc20_templates=[1],
    erc20_names=["Datatoken 1"],
    erc20_symbols=["DT1"],
    erc20_minters=[alice_wallet.address],
    erc20_fee_managers=[alice_wallet.address],
    erc20_publish_market_order_fee_addresses=[ZERO_ADDRESS],
    erc20_publish_market_order_fee_tokens=[ocean.OCEAN_address],
    erc20_caps=[ocean.to_wei(100000)],
    erc20_publish_market_order_fee_amounts=[0],
    erc20_bytess=[[b""]],
)

did = asset.did  # did contains the datatoken address
print(f"did = '{did}'")

```

## 3. Bob buys data asset, and downloads it
Now, you're Bob the data consumer.
In usual cases, Bob buys the dataset but here, let's have Alice send hhim some tokens directly.

In the same Python console as before:

```python
# Bob's wallet
bob_private_key = os.getenv('TEST_PRIVATE_KEY2')
bob_wallet = Wallet(ocean.web3, bob_private_key, config.block_confirmations, config.transaction_timeout)
print(f"bob_wallet.address = '{bob_wallet.address}'")

# Verify that Bob has ganache ETH
assert ocean.web3.eth.get_balance(bob_wallet.address) > 0, "need ganache ETH"

# Verify that Bob has ganache OCEAN
OCEAN_token = ocean.get_datatoken(ocean.OCEAN_address)
assert OCEAN_token.balanceOf(bob_wallet.address) > 0, "need ganache OCEAN"

# Mint 1 ERC20 token in consumer wallet from publisher, instead of performing a buy.
erc20_token = ocean.get_datatoken(asset.datatokens[0]["address"])
erc20_token.mint(
    account_address=bob_wallet.address,
    value=ocean.to_wei("1"),
    from_wallet=alice_wallet,
)

# Bob points to the service object
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
fee_receiver = ZERO_ADDRESS # could also be market address
service = asset.services[0]

# Bob sends his datatoken to the service
order_tx_id = ocean.assets.pay_for_access_service(
    asset,
    service,
    consume_market_order_fee_address=bob_wallet.address,
    consume_market_order_fee_token=erc20_token.address,
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
print(f"file_path = '{file_path}'") #e.g. datafile.0xAf07...
```

In console:

```
#verify that the file is downloaded
cd my_project/datafile.did:op:0xAf07...
ls branin.arff
```

Congrats to Bob for buying and consuming a data asset!

_Note_. The file is in ARFF format, used by some AI/ML tools. In this case there are two input variables (x0, x1) and one output.

```
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
