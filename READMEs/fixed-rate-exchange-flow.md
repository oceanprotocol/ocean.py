<!--
Copyright 2021 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Fixed Rate Exchange Flow

This quickstart describes fixed rate exchange flow.

It focuses on Alice's experience as a publisher, and Bob's experience as a buyer & consumer.

Here are the steps:

1.  Setup
2.  Alice creates a datatoken
3.  Alice mints & approves datatokens
4.  Bob buys at fixed rate datatokens

Let's go through each step.

## 1. Setup

### Prerequisites

-   Linux/MacOS
-   Docker, [allowing non-root users](https://www.thegeekdiary.com/run-docker-as-a-non-root-user/)
-   Python 3.8.5+

### Run barge services

In a new console:

```console
# Grab repo
git clone https://github.com/oceanprotocol/barge
cd barge

# Clean up old containers (to be sure)
docker system prune -a --volumes

# Run barge: start ganache, Provider, Aquarius; deploy contracts; update ~/.ocean
./start_ocean.sh
```

### Install the ocean.py library

In a new console that we'll call the _work_ console (as we'll use it later):

```console
# Grab ocean.py repo
cd Desktop/
git clone https://github.com/oceanprotocol/ocean.py.git
git checkout v4main

# Create your working directory. Copy artifacts.
mkdir test3
cd test3
cp -r ../ocean.py/artifacts ./

# Initialize virtual environment and activate it. Install artifacts.
python3 -m venv venv
source venv/bin/activate
chmod 777 artifacts/install-remote.sh
./artifacts/install-remote.sh

# Intermediary installation before PyPi release of V4. Install wheel first to avoid errors.
pip3 install wheel
pip3 install --no-cache-dir ../ocean.py/
```

### Set envvars

In the work console:
```console
# Set private keys of two accounts
export TEST_PRIVATE_KEY1=0x5d75837394b078ce97bc289fa8d75e21000573520bfa7784a9d28ccaae602bf8
export TEST_PRIVATE_KEY2=0xef4b441145c1d0f3b4bc6d61d29f5c6e502359481152f869247c7a4244d45209

# Needed to mint fake OCEAN for testing with ganache
export FACTORY_DEPLOYER_PRIVATE_KEY=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58

# Set the address file only for ganache
export ADDRESS_FILE=~/.ocean/ocean-contracts/artifacts/address.json

# Set network URL
export OCEAN_NETWORK_URL=http://127.0.0.1:8545

# Start python
python
```

## 2. Alice creates the datatoken


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
# Publish an NFT token
nft_token = ocean.create_nft_token(
    "NFTToken1", "NFT1", alice_wallet, "https://oceanprotocol.com/nft/"
)
token_address = nft_token.address
print(f"token_address = '{token_address}'")
```

## 3. Alice created data token & mints data tokens

In the same python console:
```python
from ocean_lib.models.models_structures import ErcCreateData
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei

# Prepare data for ERC20 token
erc20_data = ErcCreateData(
    template_index=1,
    strings=["Datatoken 1", "DT1"],
    addresses=[
        alice_wallet.address,
        alice_wallet.address,
        ZERO_ADDRESS,
        ocean.OCEAN_address,
    ],
    uints=[to_wei(200), 0],
    bytess=[b""],
)

erc20_token = nft_token.create_datatoken(erc20_data, alice_wallet)
print(f"datatoken_address = '{erc20_token.address}'")

#Mint the datatokens
erc20_token.mint(alice_wallet.address, to_wei(100), alice_wallet)
```

## 4. Bob buys at fixed rate datatokens


In the same python console:
```python
bob_private_key = os.getenv('TEST_PRIVATE_KEY2')
bob_wallet = Wallet(ocean.web3, bob_private_key, config.block_confirmations, config.transaction_timeout)
print(f"bob_wallet.address = '{bob_wallet.address}'")

# Verify that Bob has ganache ETH
assert ocean.web3.eth.get_balance(bob_wallet.address) > 0, "need ganache ETH"

OCEAN_token = ocean.get_datatoken(ocean.OCEAN_address)
```

If the `exchange_id` is not provided yet, here is the fix.
It is important to create an `exchange_id` only one time per exchange.

```python
#Create exchange_id for a new exchange
exchange_id = ocean.create_fixed_rate(
    erc20_token=erc20_token,
    basetoken=OCEAN_token,
    amount=to_wei(100),
    from_wallet=alice_wallet,
)
```

If `exchange_id` has been created before or there are other
exchanges for a certain datatoken, it can be searched by
providing the datatoken address.

```python
# Search for exchange_id from a specific block retrieved at 3rd step
# for a certain data token address (e.g. datatoken_address). Choose
# one from the list.
datatoken_address = erc20_token.address
nft_factory = ocean.get_nft_factory()
logs = nft_factory.search_exchange_by_datatoken(ocean.fixed_rate_exchange, datatoken_address)
# Optional: Filtering the logs by the exchange owner.
logs = nft_factory.search_exchange_by_datatoken(ocean.fixed_rate_exchange, datatoken_address, alice_wallet.address)
print(logs)
```

Use the `exchange_id` for buying at fixed rate.

```python
# Approve tokens for Bob
fixed_price_address = ocean.fixed_rate_exchange.address
erc20_token.approve(fixed_price_address, to_wei(100), bob_wallet)
OCEAN_token.approve(fixed_price_address, to_wei(100), bob_wallet)

tx_result = ocean.fixed_rate_exchange.buy_dt(
    exchange_id=exchange_id,
    datatoken_amount=to_wei(20),
    max_basetoken_amount=to_wei(50),
    from_wallet=bob_wallet,
    )
assert tx_result, "failed buying data tokens at fixed rate for Bob"
```
