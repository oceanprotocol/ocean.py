<!--
Copyright 2021 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Marketplace Flow

This quickstart describes a batteries-included flow including using off-chain services for metadata (Aquarius) and consuming datasets (Provider).

It focuses on Alice's experience as a publisher, and Bob's experience as a buyer & consumer.

Here are the steps:

1.  Setup
2.  Alice publishes data asset
3.  Market displays the asset for sale
4.  Bob buys data asset, and downloads it

Let's go through each step.

## 1. Setup

### Prerequisites

-   Linux/MacOS
-   Docker, [allowing non-root users](https://www.thegeekdiary.com/run-docker-as-a-non-root-user/)
-   Python 3.8.5+

### Run barge services

In a new console:

```console
#grab repo
git clone https://github.com/oceanprotocol/barge
cd barge

#clean up old containers (to be sure)
docker system prune -a --volumes

#run barge: start ganache, Provider, Aquarius; deploy contracts; update ~/.ocean
./start_ocean.sh  --with-provider2
```

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

### Install the library

In a new console that we'll call the _work_ console (as we'll use it later):

```console
#Create your working directory
mkdir test3
cd test3

#Initialize virtual environment and activate it.
python -m venv venv
source venv/bin/activate

#Install the ocean.py library. Install wheel first to avoid errors.
pip install wheel
pip install ocean-lib
```

### Set envvars

In the work console:
```console
#set private keys of two accounts
export TEST_PRIVATE_KEY1=0x5d75837394b078ce97bc289fa8d75e21000573520bfa7784a9d28ccaae602bf8
export TEST_PRIVATE_KEY2=0xef4b441145c1d0f3b4bc6d61d29f5c6e502359481152f869247c7a4244d45209

#needed to mint fake OCEAN for testing with ganache
export FACTORY_DEPLOYER_PRIVATE_KEY=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58

#set the address file only for ganache
export ADDRESS_FILE=~/.ocean/ocean-contracts/artifacts/address.json

#set network URL
export OCEAN_NETWORK_URL=http://127.0.0.1:8545

#start python
python
```

## 2. Alice publishes data asset

In the Python console:
```python
# Create Ocean instance
from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.ocean import Ocean
config = ExampleConfig.get_config()
ocean = Ocean(config)

print(f"config.network_url = '{config.network_url}'")
print(f"config.block_confirmations = {config.block_confirmations.value}")
print(f"config.metadata_cache_uri = '{config.metadata_cache_uri}'")
print(f"config.provider_url = '{config.provider_url}'")

# Create Alice's wallet
import os
from ocean_lib.web3_internal.wallet import Wallet
alice_private_key = os.getenv('TEST_PRIVATE_KEY1')
alice_wallet = Wallet(ocean.web3, alice_private_key, config.block_confirmations, config.transaction_timeout)
print(f"alice_wallet.address = '{alice_wallet.address}'")

# Mint OCEAN
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
mint_fake_OCEAN(config)
assert alice_wallet.web3.eth.get_balance(alice_wallet.address) > 0, "need ETH"

# Publish an NFT token
nft_token = ocean.create_nft_token('NFTToken1', 'NFT1', alice_wallet)
token_address = nft_token.address
print(f"token_address = '{token_address}'")

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

file_path = ocean.assets.download(
    asset.did,
    service.index,
    bob_wallet,
    order_tx_id,
    destination='./'
)
print(f"file_path = '{file_path}'") #e.g. datafile.0xAf07...
```

In console:

```console
#verify that the file is downloaded
cd test3/datafile.0xAf07...
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
