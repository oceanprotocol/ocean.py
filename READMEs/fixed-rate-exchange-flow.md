<!--
Copyright 2021 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Fixed Rate Exchange Flow

This quickstart describes fixed rate exchange flow.

It focuses on Alice's experience as a publisher, and Bob's experience as a buyer & consumer.

Here are the steps:

1.  Setup
2.  Alice creates a data token
3.  Alice mints & approves data tokens
4.  Bob buys at fixed rate data tokens

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

### Create config file

In the work console:

```console
#Create config.ini file and fill it with configuration info
[eth-network]
network = http://127.0.0.1:8545
address.file = ~/.ocean/ocean-contracts/artifacts/address.json

[resources]
metadata_cache_uri = http://localhost:5000
provider.url = http://localhost:8030
provider.address = 0x00bd138abd70e2f00903268f3db08f2d25677c9e

downloads.path = consume-downloads
```

### Set envvars

In the work console:
```console
#set private keys of two accounts
export TEST_PRIVATE_KEY1=0xbbfbee4961061d506ffbb11dfea64eba16355cbf1d9c29613126ba7fec0aed5d
export TEST_PRIVATE_KEY2=0x804365e293b9fab9bd11bddd39082396d56d30779efbb3ffb0a6089027902c4a

#start python
python
```

## 2. Alice creates the data token


In the Python console:
```python
#Create ocean instance
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
assert alice_wallet.web3.eth.get_balance(alice_wallet.address) > 0, "need ETH"
data_token = ocean.create_data_token('DataToken1', 'DT1', alice_wallet, blob=ocean.config.metadata_cache_uri)
token_address = data_token.address
print(f"token_address = '{token_address}'")
```

## 3. Alice mints & approve data tokens

In the same python console:
```python
#Mint the datatokens
data_token.mint_tokens(alice_wallet.address, 100.0, alice_wallet)
from ocean_lib.ocean.util import to_base_18
data_token.approve(ocean.exchange._exchange_address, to_base_18(100.0), alice_wallet)
```

## 4. Bob buys at fixed rate data tokens


In the same python console:
```python
bob_wallet = Wallet(ocean.web3, private_key=os.getenv('TEST_PRIVATE_KEY2'))
print(f"bob_wallet.address = '{bob_wallet.address}'")
 
#Verify that Bob has ganache ETH
assert ocean.web3.eth.get_balance(bob_wallet.address) > 0, "need ganache ETH"

from ocean_lib.models.btoken import BToken #BToken is ERC20
OCEAN_token = BToken(ocean.web3, ocean.OCEAN_address)
assert OCEAN_token.balanceOf(alice_wallet.address) > 0, "need OCEAN"
assert OCEAN_token.balanceOf(bob_wallet.address) > 0, "need ganache OCEAN"
```

If the `exchange_id` is not provided yet, here is the fix.
It is important to create an `exchange_id` only one time per exchange.

```python
#Create exchange_id for a new exchange 
exchange_id = ocean.exchange.create(token_address, 0.1, alice_wallet)
```

Use the `exchange_id` for buying at fixed rate.

```python
tx_result = ocean.exchange.buy_at_fixed_rate(2.0, bob_wallet, 5.0, exchange_id, token_address, alice_wallet.address)
assert tx_result, "failed buying data tokens at fixed rate for Bob"
```