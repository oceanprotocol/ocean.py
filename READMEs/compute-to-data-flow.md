<!--
Copyright 2021 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Compute to Data Flow

Here are the steps:

1.  Setup
2.  Alice publishes data asset & mints data tokens
3.  Alice transfers some data tokens to Bob
4.  Bob consumes in a Compute to Data setting

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
network = ganache
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

#start python
python
```

## 2. Alice publishes data asset & mints data tokens for Bob

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
bob_wallet = Wallet(ocean.web3, private_key=os.getenv('TEST_PRIVATE_KEY2'))
print(f"alice_wallet.address = '{alice_wallet.address}'")
print(f"bob_wallet.address = '{bob_wallet.address}'")

#Publish a datatoken
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
asset = ocean.assets.create(
  metadata,
  alice_wallet,
  service_descriptors=[download_service],
  data_token_address=token_address)
assert token_address == asset.data_token_address

did = asset.did  # did contains the datatoken address
print(f"did = '{did}'")

#Mint the datatokens
data_token.mint_tokens(alice_wallet.address, 100.0, alice_wallet)
```

In the same console, Alice will transfer some data tokens to Bob.

## 3.  Alice transfers some data tokens to Bob

```python
from ocean_lib.exceptions import VerifyTxFailed
assert data_token.balanceOf(alice_wallet.address) < 20, "need ETH"
assert data_token.allowance(alice_wallet.address, bob_wallet.address) < 20
print(f"bob_balance: {ocean.web3.eth.get_balance(bob.wallet.address)}")
tx_id = data_token.transferFrom(alice_wallet.address, bob_wallet.address, 20, alice_wallet)
if data_token.get_tx_receipt(ocean.web3, tx_id).status != 1:
    raise VerifyTxFailed(
        f"Transferring datatokens failed."
    )
print(f"tx_id: {tx_id}")
print(f"bob_balance after the transfer: {ocean.web3.eth.get_balance(bob_wallet.address)}") 
```