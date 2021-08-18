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

### Set up contracts

Create a file called `test3/config.ini` and fill it as follows.

```text
[eth-network]
network = http://127.0.0.1:8545
address.file = ~/.ocean/ocean-contracts/artifacts/address.json

[resources]
metadata_cache_uri = http://localhost:5000
provider.url = http://localhost:8030
provider.address = 0x00bd138abd70e2f00903268f3db08f2d25677c9e

downloads.path = consume-downloads
```

In the work console:
```console
#set private keys of two accounts
export TEST_PRIVATE_KEY1=0xbbfbee4961061d506ffbb11dfea64eba16355cbf1d9c29613126ba7fec0aed5d
export TEST_PRIVATE_KEY2=0x804365e293b9fab9bd11bddd39082396d56d30779efbb3ffb0a6089027902c4a

#needed to mint fake OCEAN
export FACTORY_DEPLOYER_PRIVATE_KEY=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58

#start python
python
```

## 2. Alice publishes data asset

In the Python console:
```python
#create ocean instance
from ocean_lib.config import Config
from ocean_lib.ocean.ocean import Ocean
config = Config('config.ini')
ocean = Ocean(config)

print(f"config.network_url = '{config.network_url}'")
print(f"config.metadata_cache_uri = '{config.metadata_cache_uri}'")
print(f"config.provider_url = '{config.provider_url}'")

#Alice's wallet
import os
from ocean_lib.web3_internal.wallet import Wallet
alice_wallet = Wallet(ocean.web3, private_key=os.getenv('TEST_PRIVATE_KEY1'))
print(f"alice_wallet.address = '{alice_wallet.address}'")

#Mint OCEAN
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
mint_fake_OCEAN(config)

#Publish a datatoken
assert alice_wallet.web3.eth.get_balance(alice_wallet.address) > 0, "need ETH"
data_token = ocean.create_data_token('DataToken1', 'DT1', alice_wallet, blob=ocean.config.metadata_cache_uri)
token_address = data_token.address
print(f"token_address = '{token_address}'")

#Specify metadata and service attributes, using the Branin test dataset
date_created = "2019-12-28T10:55:11Z"
metadata =  {
    "main": {
        "type": "dataset", "name": "branin", "author": "Trent",
        "license": "CC0: Public Domain", "dateCreated": date_created,
        "files": [{"index": 0, "contentType": "text/text",
	           "url": "https://raw.githubusercontent.com/trentmc/branin/master/branin.arff"}]}
}
service_attributes = {
        "main": {
            "name": "dataAssetAccessServiceAgreement",
            "creator": alice_wallet.address,
            "timeout": 3600 * 24,
            "datePublished": date_created,
            "cost": 1.0, # <don't change, this is obsolete>
        }
    }

#Publish metadata and service attributes on-chain.
# The service urls will be encrypted before going on-chain.
# They're only decrypted for datatoken owners upon consume.
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.common.agreements.service_factory import ServiceDescriptor

service_endpoint = DataServiceProvider.get_url(ocean.config)
download_service = ServiceDescriptor.access_service_descriptor(service_attributes, service_endpoint)
assert alice_wallet.web3.eth.get_balance(alice_wallet.address) > 0, "need ETH"
asset = ocean.assets.create(
  metadata,
  alice_wallet,
  service_descriptors=[download_service],
  data_token_address=token_address)
assert token_address == asset.data_token_address

did = asset.did  # did contains the datatoken address
print(f"did = '{did}'")

#Mint the datatokens
from ocean_lib.web3_internal.currency import to_wei
data_token.mint(alice_wallet.address, to_wei("100.0"), alice_wallet)

#In the create() step below, Alice needs ganache OCEAN. Ensure she has it.
from ocean_lib.models.btoken import BToken #BToken is ERC20
OCEAN_token = BToken(ocean.web3, ocean.OCEAN_address)
assert OCEAN_token.balanceOf(alice_wallet.address) > 0, "need OCEAN"

#Post the asset for sale. This does many blockchain txs: create base
# pool, bind OCEAN and datatoken, add OCEAN and datatoken liquidity,
# and finalize the pool.
pool = ocean.pool.create(
   token_address,
   data_token_amount=to_wei("100.0"),
   OCEAN_amount=to_wei("10.0"),
   from_wallet=alice_wallet
)
pool_address = pool.address
print(f"pool_address = '{pool_address}'")
```

## 3. Marketplace displays asset for sale

Now, you're the Marketplace operator. Here's how to get info about the data asset.

In the same Python console as before:

```python
#point to services
from ocean_lib.common.agreements.service_types import ServiceTypes
asset = ocean.assets.resolve(did)
service1 = asset.get_service(ServiceTypes.ASSET_ACCESS)

#point to pool
pool = ocean.pool.get(ocean.web3, pool_address)

#To access a data service, you need 1.0 datatokens.
#Here, the market retrieves the datatoken price denominated in OCEAN.
OCEAN_address = ocean.OCEAN_address
price_in_OCEAN = ocean.pool.calcInGivenOut(
    pool_address, OCEAN_address, token_address, token_out_amount=to_wei("1.0"))
print(f"Price of 1 datatoken is {price_in_OCEAN} OCEAN")
```

## 4.  Bob buys data asset, and downloads it

Now, you're Bob the data consumer.

In the same Python console as before:

```python
#Bob's wallet
bob_wallet = Wallet(ocean.web3, private_key=os.getenv('TEST_PRIVATE_KEY2'))
print(f"bob_wallet.address = '{bob_wallet.address}'")

#Verify that Bob has ganache ETH
assert ocean.web3.eth.get_balance(bob_wallet.address) > 0, "need ganache ETH"

#Verify that Bob has ganache OCEAN
assert OCEAN_token.balanceOf(bob_wallet.address) > 0, "need ganache OCEAN"

#Bob buys 1.0 datatokens - the amount needed to consume the dataset.
data_token = ocean.get_data_token(token_address)
ocean.pool.buy_data_tokens(
    pool_address,
    amount=to_wei("1.0"), # buy 1.0 datatoken
    max_OCEAN_amount=to_wei("10.0"), # pay up to 10.0 OCEAN
    from_wallet=bob_wallet
)

from ocean_lib.web3_internal.currency import wei_and_pretty_ether
print(f"Bob has {wei_and_pretty_ether(data_token.balanceOf(bob_wallet.address), data_token.symbol())} datatokens.")

from ocean_lib.web3_internal.currency import to_wei
assert data_token.balanceOf(bob_wallet.address) >= to_wei("1.0"), "Bob didn't get 1.0 datatokens"

#Bob points to the service object
fee_receiver = None # could also be market address
from ocean_lib.common.agreements.service_types import ServiceTypes
asset = ocean.assets.resolve(did)
service = asset.get_service(ServiceTypes.ASSET_ACCESS)

#Bob sends his datatoken to the service
quote = ocean.assets.order(asset.did, bob_wallet.address, service_index=service.index)
order_tx_id = ocean.assets.pay_for_service(
    ocean.web3,
    quote.amount, quote.data_token_address, asset.did, service.index, fee_receiver, bob_wallet, None)
print(f"order_tx_id = '{order_tx_id}'")

#Bob downloads. If the connection breaks, Bob can request again by showing order_tx_id.
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
