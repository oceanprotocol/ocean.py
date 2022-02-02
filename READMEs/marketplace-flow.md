<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Marketplace Flow

This quickstart describes a batteries-included flow including using off-chain services for metadata (Aquarius) and consuming datasets (Provider).

For pool creation, it is used as base token, OCEAN token.
The base token can be changed into something else, such as USDC, DAI etc., but
it will require an extra fee.

It focuses on Alice's experience as a publisher, and Bob's experience as a buyer & consumer.

Here are the steps:

1.  Setup
2.  Alice publishes data asset
3.  Market displays the asset for sale
4.  Bob buys data asset, and downloads it

Let's go through each step.

## 1. Setup

### First steps

To get started with this guide, please refer to [datatokens-flow](datatokens-flow.md) and complete the following steps :
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

Set the required enviroment variables as described in [datatokens-flow](datatokens-flow.md):
- [x] Setup : Set envvars

## 2. Marketplace flow

In your project folder (i.e. my_project from `Install the library` step) and in the work console where you set envvars, run the following:

Please refer to [datatokens-flow](datatokens-flow.md) and complete the following steps :
- [x] 2.1 Create an erc721 NFT token

Then in the same python console:
```python
# Prepare data for ERC20 token
from ocean_lib.models.models_structures import CreateErc20Data
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
erc20_data = CreateErc20Data(
    template_index=1,
    strings=["Datatoken 1", "DT1"],
    addresses=[
        alice_wallet.address,
        alice_wallet.address,
        ZERO_ADDRESS,
        ocean.OCEAN_address,
    ],
    uints=[ocean.to_wei(100000), 0],
    bytess=[b""],
)

# Specify metadata and services, using the Branin test dataset
date_created = "2021-12-28T10:55:11Z"

metadata = {
    "created": date_created,
    "updated": date_created,
    "description": "Branin dataset",
    "name": "Branin dataset",
    "type": "dataset",
    "author": "Treunt",
    "license": "CC0: PublicDomain",
}

# ocean.py offers multiple file types, but a simple url file should be enough for this example
from ocean_lib.agreements.file_objects import UrlFile
url_file = UrlFile(
    url="https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"
)

# Encrypt file(s) using provider
encrypted_files = ocean.assets.encrypt_files([url_file])


# Publish asset with services on-chain.
# The download (access service) is automatically created, but you can explore other options as well
asset = ocean.assets.create(
    metadata, alice_wallet, encrypted_files, erc20_tokens_data=[erc20_data]
)

did = asset.did  # did contains the datatoken address
print(f"did = '{did}'")

```

In order to encrypt the entire asset, when using a private market or metadata cache, use the encrypt keyword.
Same for compression and you can use a combination of the two. E.g:
`asset = ocean.assets.create(..., encrypt_flag=True)` or `asset = ocean.assets.create(..., compress_flag=True)`

In the following steps we will create a pool from the created token, in order to allow another user
to order this access token.
```python
erc20_token = ocean.get_datatoken(asset.get_service("access").datatoken)
OCEAN_token = ocean.get_datatoken(ocean.OCEAN_address)

ss_params = [
    ocean.to_wei(1),
    OCEAN_token.decimals(),
    ocean.to_wei(10000),
    2500000,
    ocean.to_wei(2000)
]

swap_fees = [ocean.to_wei("0.01"), ocean.to_wei("0.01")]
bpool = ocean.create_pool(erc20_token, OCEAN_token, ss_params, swap_fees, alice_wallet)
print(f"BPool address: {bpool.address}")

```

## 3. Marketplace displays asset for sale

Now, you're the Marketplace operator. Here's how to get info about the data asset.

In the same Python console as before:

```python
price_in_OCEAN = bpool.get_amount_in_exact_out(
    OCEAN_token.address,
    erc20_token.address,
    ocean.to_wei(1),
    ocean.to_wei("0.01")
)

from ocean_lib.web3_internal.currency import pretty_ether_and_wei
print(f"Price of 1 {erc20_token.symbol()} is {pretty_ether_and_wei(price_in_OCEAN, 'OCEAN')}")
```

## 4. Bob buys data asset, and downloads it
Now, you're Bob the data consumer.

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

# Bob buys 1.0 datatokens - the amount needed to consume the dataset.
OCEAN_token.approve(bpool.address, ocean.to_wei("10000"), from_wallet=bob_wallet)

bpool.swap_exact_amount_out(
    [OCEAN_token.address, erc20_token.address, ZERO_ADDRESS],
    [
        ocean.to_wei(10),
        ocean.to_wei(1),
        ocean.to_wei(10),
        0,
    ],
    from_wallet=bob_wallet,
)
assert erc20_token.balanceOf(bob_wallet.address) >= ocean.to_wei(
    1
), "Bob didn't get 1.0 datatokens"

# Bob points to the service object
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
fee_receiver = ZERO_ADDRESS # could also be market address
asset = ocean.assets.resolve(did)
service = asset.get_service("access")

# Bob sends his datatoken to the service
service = asset.get_service("access")
order_tx_id = ocean.assets.pay_for_service(
    asset, service, bob_wallet
)
print(f"order_tx_id = '{order_tx_id}'")

# Bob downloads. If the connection breaks, Bob can request again by showing order_tx_id.
file_path = ocean.assets.download_asset(
    asset,
    service.service_endpoint,
    bob_wallet,
    './',
    order_tx_id
)

print(f"file_path = '{file_path}'") #e.g. datafile.0xAf07...
```

In console:

```console
#verify that the file is downloaded
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
