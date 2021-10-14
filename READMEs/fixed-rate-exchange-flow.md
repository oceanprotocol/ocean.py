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
./start_ocean.sh
```

### Install the ocean.py library

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

## 2. Alice creates the data token


In the Python console:
```python
#Create ocean instance
from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.ocean import Ocean
config = ExampleConfig.get_config()
ocean = Ocean(config)

print(f"config.network_url = '{config.network_url}'")
print(f"config.block_confirmations = {config.block_confirmations.value}")
print(f"config.metadata_cache_uri = '{config.metadata_cache_uri}'")
print(f"config.provider_url = '{config.provider_url}'")

#Alice's wallet
import os
from ocean_lib.web3_internal.wallet import Wallet
alice_private_key = os.getenv('TEST_PRIVATE_KEY1')
alice_wallet = Wallet(ocean.web3, alice_private_key, config.block_confirmations, config.transaction_timeout)
print(f"alice_wallet.address = '{alice_wallet.address}'")

#Mint OCEAN for ganache only
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
mint_fake_OCEAN(config)

assert alice_wallet.web3.eth.get_balance(alice_wallet.address) > 0, "need ETH"
data_token = ocean.create_data_token('DataToken1', 'DT1', alice_wallet, blob=config.metadata_cache_uri)
token_address = data_token.address
print(f"token_address = '{token_address}'")
```

## 3. Alice mints & approve data tokens

In the same python console:
```python
#Mint the datatokens
from ocean_lib.web3_internal.currency import to_wei
data_token.mint(alice_wallet.address, to_wei(100), alice_wallet)
data_token.approve(ocean.exchange._exchange_address, to_wei(100), alice_wallet)
```

## 4. Bob buys at fixed rate data tokens


In the same python console:
```python
bob_private_key = os.getenv('TEST_PRIVATE_KEY2')
bob_wallet = Wallet(ocean.web3, bob_private_key, config.block_confirmations, configtransaction_timeout)
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
exchange_id = ocean.exchange.create(token_address, to_wei("0.1"), alice_wallet)
```

If `exchange_id` has been created before or there are other
exchanges for a certain data token, it can be searched by
providing the data token address.

```python
#Search for exchange_id for a certain data token address (e.g. token_address).
logs = ocean.exchange.search_exchange_by_data_token(token_address)
print(logs)
#E.g. First exchange is the wanted one.
exchange_id = logs[0].args.exchangeId
```
_Optional:_ Filtering the logs by the exchange owner.
```python
filtered_logs = list(filter(lambda log: log.args.exchangeOwner == alice_wallet.address, logs))
print(filtered_logs)
```

Use the `exchange_id` for buying at fixed rate.

```python
tx_result = ocean.exchange.buy_at_fixed_rate(to_wei(2), bob_wallet, to_wei(5), exchange_id, token_address, alice_wallet.address)
assert tx_result, "failed buying data tokens at fixed rate for Bob"
```