<!--
Copyright 2021 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Publish your first datatoken

Steps:

1.  **Install**
2.  **Run the services**
3.  **Publish datatokens!**

## 1. Install 

### 1.1 Prerequisites

-   Linux/MacOS
-   Docker
-   Python 3.8.5

### 1.2 Install the library

In a console:

```console
#Initialize virtual environment and activate it.
python -m venv venv
source venv/bin/activate

#Install the ocean.py library
pip install ocean-lib
```

## 2. Run the services

Use Ocean Barge to run local Ethereum node with Ocean contracts, Aquarius, and Provider.

In a new console:

```console
#grab repo
git clone https://github.com/oceanprotocol/barge
cd barge

#clean up old containers (to be sure)
docker system prune -a --volumes

#run barge with provider on
./start_ocean.sh  --with-provider2
```


## 3. Publish datatokens!

Set envvars. In a new console:
```console
export TEST_PRIVATE_KEY1=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58
export NETWORK_URL=ganache
```

In Python console:

```python
import os
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.wallet import Wallet

private_key = os.getenv('TEST_PRIVATE_KEY1')
config = {'network': os.getenv('NETWORK_URL')}
ocean = Ocean(config)

print("create wallet: begin")
wallet = Wallet(ocean.web3, private_key=private_key)
print(f"create wallet: done. Its address is {wallet.address}")

print("create datatoken: begin.")
datatoken = ocean.create_data_token("Dataset name", "dtsymbol", from_wallet=wallet) 
print(f"created datatoken: done. Its address is {datatoken.address}")
```

If you made it to the end: congrats, you have created your first Ocean datatoken! 🐋

