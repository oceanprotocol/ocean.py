<!--
Copyright 2021 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Publish datatoken

## Run the services

In a new console:

```console
#grab repo
git clone https://github.com/oceanprotocol/barge
cd barge

#clean up old containers (to be sure)
docker system prune -a --volumes

#run barge (runs ganache, Provider, Aquarius)
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
export TEST_PRIVATE_KEY1=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58

#go into python
python
```

## Publish datatokens

In the Python console:

```python
import os
from ocean_lib.config import Config
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.wallet import Wallet

private_key = os.getenv('TEST_PRIVATE_KEY1')
config = Config('config.ini')
ocean = Ocean(config)

print("create wallet: begin")
wallet = Wallet(ocean.web3, private_key=private_key)
print(f"create wallet: done. Its address is {wallet.address}")

print("create datatoken: begin.")
datatoken = ocean.create_data_token("Dataset name", "dtsymbol", from_wallet=wallet) 
print(f"created datatoken: done. Its address is {datatoken.address}")
```
Congrats, you've created your first Ocean datatoken! 🐋

