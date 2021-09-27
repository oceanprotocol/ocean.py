<!--
Copyright 2021 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Dispenser Flow

This quickstart describes the dispenser flow.

It focuses on Alice's experience as a publisher.

Here are the steps:

1.  Setup
2.  Alice creates a data token
3.  Dispenser creation & activation

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
export TEST_PRIVATE_KEY1=0x5d75837394b078ce97bc289fa8d75e21000573520bfa7784a9d28ccaae602bf8

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
print(f"config.metadata_cache_uri = '{config.metadata_cache_uri}'")
print(f"config.provider_url = '{config.provider_url}'")
print(f"config.network_name = '{config.network_name}'")

#Alice's wallet
import os
from ocean_lib.web3_internal.wallet import Wallet
alice_private_key = os.getenv('TEST_PRIVATE_KEY1')
alice_wallet = Wallet(ocean.web3, alice_private_key, config.block_confirmations)
print(f"alice_wallet.address = '{alice_wallet.address}'")

#Mint OCEAN for ganache only
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
mint_fake_OCEAN(config)

assert alice_wallet.web3.eth.get_balance(alice_wallet.address) > 0, "need ETH"

data_token = ocean.create_data_token('DataToken1', 'DT1', alice_wallet, blob=ocean.config.metadata_cache_uri)
token_address = data_token.address
print(f"token_address = '{token_address}'")
```

### 3. Dispenser creation & activation

In the same python console:
```python
from ocean_lib.web3_internal.contract_utils import get_contracts_addresses
from ocean_lib.models.dispenser import DispenserContract
from ocean_lib.web3_internal.currency import to_wei

contracts_addresses = get_contracts_addresses(config.network_name, config.address_file)
assert contracts_addresses, "invalid network."
print(f"contracts_addresses = {contracts_addresses}")
#Create the dispenser
dispenser_address = contracts_addresses["Dispenser"]
dispenser = DispenserContract(alice_wallet.web3, dispenser_address)

#Activate the dispenser
dispenser.activate(token_address, to_wei(100), to_wei(100), alice_wallet)
assert dispenser.is_active(token_address), f"dispenser is not active for {token_address} data token."

#Mint the datatokens for the dispenser
data_token.mint(dispenser_address, to_wei(100), alice_wallet)
data_token.approve(dispenser_address, to_wei(100), alice_wallet)

#Dispense
tx_result = dispenser.dispense(token_address, to_wei(50), alice_wallet)
assert tx_result, "failed to dispense data tokens for Alice."
print(f"tx_result = '{tx_result}'")
```


