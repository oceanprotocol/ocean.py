<!--
Copyright 2021 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->
<!--

# Quickstart: Marketplace Flow with compute-to-data

This tutorial demonstrates publishing a dataset with `compute` service

We will be connecting to the `rinkeby` test net and the Ocean Protocol
supporting services.

Here's the steps:

1.  Setup
2.  Alice publishes assets for data services (= publishes a datatoken contract and metadata)
3.  Alice mints 100 tokens
4.  Alice makes datatokens available for sale in a Balancer pool
5.  Marketplace displays the asset with the available services and price of datatoken
6.  Value swap: Bob buys datatokens from marketplace
7.  Bob uses a service by spending datatoken he just purchased (download)

Let's go through each step.

## 0. Prerequisites and Installation

In a new console:
```console
#Create your working directory
mkdir test
cd test

#Initialize virtual environment and activate it.
python -m venv venv
source venv/bin/activate

#Install the ocean.py library
pip install ocean-lib
```
Use ethereum accounts with some ether balance on rinkeby. You can get rinkeby ether using
this [faucet](https://www.rinkeby.io/#faucet). Otherwise, run `ganache-cli` and replace
`rinkeby` with `ganache` when following the steps below.

Also you will need rinkeby ocean for interacting with Balancer DataToken-Ocean Pools. Get your Test Ocean 
using this [faucet](https://faucet.rinkeby.oceanprotocol.com/).

Initalize 2 different Ethereum Addresses on Rİnkeby with Faucets. We'll call them Alice and Bob.

## 1. Initialize services

This quickstart treats the publisher/provider service, metadata cache, and marketplace as
externally-run services. We will be using Ocean's provider and aquarius, with links to use services on rinkeby.
For convenience, we run Market locally. 

On a new console:

[Market app](https://github.com/oceanprotocol/market)
```console
    git clone https://github.com/oceanprotocol/market.git
    cd market
    npm install
    npm start
```

Access the market app in the browser at `http://localhost:8000`. Switch to rinkeby network on metamask, if you would like to see newly published DataTokens in the following steps.

## 2. Alice publishes assets for data services (= publishes a DataToken contract)

In a python console or Jupyter Notebook:
```python
from ocean_utils.agreements.service_factory import ServiceDescriptor

from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.data_provider.data_service_provider import DataServiceProvider

#Alice's config is using 
providerUri = 'https://provider.mainnet.oceanprotocol.com'
providerUri_rinkeby = 'https://provider.rinkeby.oceanprotocol.com'
config={
        'network': 'rinkeby',
        'metadataStoreUri': 'https://aquarius.rinkeby.oceanprotocol.com',
        'providerUri': providerUri_rinkeby
        }
ocean = Ocean(config=config)

# Alice needs some ether and Ocean token:
PRIV_KEY_0='16b8bda3e5163fc20a957aaf859286fc3f7a0948b2c3c77bfe029f492c1d9ec6' #change this if you need to use another publisher
alice_wallet = Wallet(ocean.web3, private_key=PRIV_KEY_0)

data_token = ocean.create_data_token('DataToken0', 'DT0', alice_wallet, blob=ocean.config.metadata_store_url)
token_address = data_token.address

# `ocean.assets.create` will encrypt the URLs using the provider's encrypt service endpoint and update
# the asset before pushing to metadata store
# `ocean.assets.create` will require that token_address is a valid DataToken contract address, unless token_address
# is not provided then the `create` method will first create a new data token and use it in the new
# asset.
metadata =  {
    "main": {
        "type": "dataset", "name": "Compute-flow Example", "author": "User",
        "license": "CC0: Public Domain", "dateCreated": "2012-02-01T10:55:11Z",
        "files": [
            { "index": 0, "contentType": "application/zip", "url": "https://s3.amazonaws.com/datacommons-seeding-us-east/10_Monkey_Species_Small/assets/training.zip"},
            { "index": 1, "contentType": "text/text", "url": "https://s3.amazonaws.com/datacommons-seeding-us-east/10_Monkey_Species_Small/assets/monkey_labels.txt"},
            { "index": 2, "contentType": "application/zip", "url": "https://s3.amazonaws.com/datacommons-seeding-us-east/10_Monkey_Species_Small/assets/validation.zip"}]}
}

# Prepare attributes for the download service including the cost in DataTokens
service_attributes = {
        "main": {
            "name": "dataAssetAccessServiceAgreement",
            "creator": alice_wallet.address,
            "cost": 1.0, # service cost is 1.0 tokens
            "timeout": 3600 * 24,
            "datePublished": metadata["main"]['dateCreated']
        }
    }

service_endpoint = DataServiceProvider.get_url(ocean.config)
download_service = ServiceDescriptor.access_service_descriptor(service_attributes, service_endpoint)
asset = ocean.assets.create(metadata, alice_wallet, service_descriptors=[download_service], data_token_address=token_address)
assert token_address == asset.data_token_address

did = asset.did  # did contains the datatoken address
print(did)
```
-->
# Quickstart: Publish datatoken

## Prerequisites

-   Linux/MacOS
-   Docker, [allowing non-root users](https://www.thegeekdiary.com/run-docker-as-a-non-root-user/)
-   Python 3.8.5+

## Run barge services

Ocean `barge` runs ganache (local blockchain), Provider (data service), and Aquarius (metadata cache).

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

## Create config file

Create a file called `config.ini` and fill it as follows.

```text
[eth-network]
network = ganache
artifacts.path = ~/.ocean/ocean-contracts/artifacts
address.file = ~/.ocean/ocean-contracts/artifacts/address.json
```

## Install the library, set envvars

In a new console:

```console
#Initialize virtual environment and activate it.
python -m venv venv
source venv/bin/activate

#Install the ocean.py library
pip install ocean-lib

#set envvars
export TEST_PRIVATE_KEY1=0x16b8bda3e5163fc20a957aaf859286fc3f7a0948b2c3c77bfe029f492c1d9ec6
export TEST_PRIVATE_KEY1=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58

#go into python
python
```

## 2. Alice publishes a datatoken

In the Python console:

```python
import os
from ocean_lib.config import Config
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.wallet import Wallet

private_key = os.getenv('TEST_PRIVATE_KEY1')
private_key_2 = os.getenv('TEST_PRIVATE_KEY2')
config = Config('config.ini')
ocean = Ocean(config)

print("create wallet: begin")
alice_wallet = Wallet(ocean.web3, private_key=private_key)
bob_wallet = Wallet(ocean.web3, private_key=private_key_2)
print(f"create wallet: done. Its address is {wallet.address}")

print("create datatoken: begin.")
datatoken = ocean.create_data_token("Dataset name", "dtsymbol", from_wallet=wallet) 
print(f"created datatoken: done. Its address is {datatoken.address}")
```

Congrats, you've created your first Ocean datatoken! 🐋

<!--
Checkout `http://localhost:8000` to see your new DataToken.
For legacy support, you can also use `metadataStoreUri` instead of `metadataCacheUri`.
-->

## 3. Alice transfers datatoken to Bob

```python
datatoken.mint_tokens(alice_wallet.address, 100.0, alice_wallet)
datatoken.transfer(alice_wallet.address,bob_wallet,50.0)
```

<!-- ## 4. Alice creates a pool for trading her new data tokens

```python
pool = ocean.pool.create(
   token_address,
   data_token_amount=99.0,
   OCEAN_amount=10.0,
   from_wallet=alice_wallet
)
pool_address = pool.address
print(f'DataToken @{datatoken.address} has a `pool` available @{pool_address}')

``` -->

<!-- ## 5. Marketplace posts asset for sale using price obtained from balancer pool


```python
from ocean_utils.agreements.service_types import ServiceTypes

from ocean_lib.ocean.ocean import Ocean
from ocean_lib.ocean.util import from_base_18
from ocean_lib.models.bpool import BPool

# Market's config
market_ocean = Ocean(config=config)

# did = 'did:op:2f93D0245B7aaD99b65c7DaC19C03B28CeAb4c36'  # from step 3,
# pool_address = '0xC4504eb21218BdbD23dec84D6B75986C1424A30d'  # from step 4,
asset = market_ocean.assets.resolve(did)
service1 = asset.get_service(ServiceTypes.ASSET_ACCESS)
pool = market_ocean.pool.get(pool_address)
# price in OCEAN tokens per data token
OCEAN_address = market_ocean.pool.ocean_address
price_in_OCEAN = market_ocean.pool.calcInGivenOut(
    pool_address, OCEAN_address, token_address, token_out_amount=1.0
)

``` -->

<!-- ## 6. Value swap: Bob buys datatokens from marketplace (using datatoken <> OCEAN balancer pool)

```python
from ocean_lib.ocean.util import to_base_18
from ocean_lib.web3_internal.wallet import Wallet

bob_wallet = Wallet(ocean.web3, private_key="c594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58")
datatoken = market_ocean.get_data_token(token_address)
# This assumes bob_wallet already has sufficient OCEAN tokens to buy the data token. OCEAN tokens
# can be obtained through a crypto exchange or an on-chain pool such as balancer or uniswap on mainnet, 
# you need to get test Ocean if you are using a test network such as Rinkeby.
market_ocean.pool.buy_data_tokens(
    pool_address,
    amount=1.0, # buy one data token
    max_OCEAN_amount=10.0, # pay up to s10 OCEAN tokens
    from_wallet=bob_wallet
)
```

and we will wait until bob has some DataTokens:
```python
bobsToken=datatoken.token_balance(bob_wallet.address)
while(bobsToken<=0):
    bobsToken=datatoken.token_balance(bob_wallet.address)
    time.sleep(5)
print(f'bob has {datatoken.token_balance(bob_wallet.address)} datatokens.')
``` -->

## 5. Bob uses a service from the asset he just purchased (download)

```python
market_address = '0xD679a72Ff5cE7EA1f4725ADb3f57c9aDb8F51738' # Market address can be anyone, that will receive the market fee. Leave empty if you want
service = asset.get_service(ServiceTypes.ASSET_ACCESS)  # asset from step 5
quote = market_ocean.assets.order(asset.did, bob_wallet.address, service_index=service.index)
order_tx_id = market_ocean.assets.pay_for_service(
    quote.amount, quote.data_token_address, asset.did, service.index, market_address, bob_wallet
)
file_path = market_ocean.assets.download(
    asset.did,
    service.index,
    bob_wallet,
    order_tx_id,
    destination='./'
)
```
Now check out the Market for new datatoken; Alice's address & Bob's address to see the details of the Token exchange.  