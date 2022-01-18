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
from ocean_lib.models.models_structures import ErcCreateData
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
config = ExampleConfig.get_config()
ocean = Ocean(config)

print(f"config.network_url = '{config.network_url}'")
print(f"config.block_confirmations = {config.block_confirmations.value}")
print(f"config.metadata_cache_uri = '{config.metadata_cache_uri}'")
print(f"config.provider_url = '{config.provider_url}'")
print(f"config.network_name = '{config.network_name}'")

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
erc721_token = ocean.create_nft_token("NFTToken1", "NFT1", alice_wallet)
token_address = erc721_token.address
print(f"token_address = '{token_address}'")

# Prepare data for ERC20 token
cap = to_wei(100)
erc20_data = ErcCreateData(
    template_index=1,  # default value
    strings=["ERC20DT1", "ERC20DT1Symbol"],  # name & symbol for ERC20 token
    addresses=[
        alice_wallet.address,  # minter address
        alice_wallet.address,  # fee manager for this ERC20 token
        alice_wallet.address,  # publishing Market Address
        ZERO_ADDRESS,  # publishing Market Fee Token
    ],
    uints=[cap, 0],
    bytess=[b""],
)
erc20_token = erc721_token.create_data_token(
    erc20_data=erc20_data, from_wallet=alice_wallet
)
```

### 3. Dispenser creation & activation

In the same python console:
```python
from ocean_lib.models.dispenser import Dispenser
from ocean_lib.models.models_structures import DispenserData
from ocean_lib.ocean.util import get_address_of_type

# Get the dispenser
dispenser = Dispenser(ocean.web3, get_address_of_type(config, "Dispenser"))

max_amount = to_wei(50)
dispenser_data = DispenserData(
    dispenser_address=dispenser.address,
    max_balance=max_amount,
    max_tokens=max_amount,
    allowed_swapper=ZERO_ADDRESS,
)

# Create dispenser
erc20_token.create_dispenser_with_mint(dispenser_data, from_wallet=alice_wallet)

dispenser_status = dispenser.status(erc20_token.address)
assert dispenser_status[0] is True
assert dispenser_status[1] == alice_wallet.address
assert dispenser_status[2] is True

initial_balance = erc20_token.balanceOf(alice_wallet.address)
assert initial_balance == 0
dispenser.dispense_tokens(
    erc20_token=erc20_token, amount=max_amount, consumer_wallet=alice_wallet
)
assert erc20_token.balanceOf(alice_wallet.address) == max_amount
```


