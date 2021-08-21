<!--
Copyright 2021 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Publish datatoken

## Prerequisites

-   Linux/MacOS
-   [Docker](https://docs.docker.com/engine/install/), [Docker Compose](https://docs.docker.com/compose/install/), [allowing non-root users](https://www.thegeekdiary.com/run-docker-as-a-non-root-user/)
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
address.file = ~/.ocean/ocean-contracts/artifacts/address.json
```

## Install the library, set envvars

In a new console:

```console
#Initialize virtual environment and activate it.
python -m venv venv
source venv/bin/activate

#Install the ocean.py library. Install wheel first to avoid errors.
pip install wheel
pip install ocean-lib

#set envvars
export TEST_PRIVATE_KEY1=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58

#go into python
python
```

## Publish asset & algorithm, run C2D

In the Python console:

```python
import os
from ocean_lib.config import Config
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.wallet import Wallet

private_key = os.getenv('TEST_PRIVATE_KEY1')
config = Config('config.ini')
ocean = Ocean(config)

#create wallet
wallet = Wallet(ocean.web3, private_key=private_key)

#publish your dataset, including metadata
### npm run cli publish metadata/simpleDataset.json 
datatoken = ocean.create_data_token("Dataset name", "dtsymbol", from_wallet=wallet)
FIXME

#publish your python algorithm
### npm run cli publishAlgo metadata/pythonAlgo.json
FIXME

#create algorithm asset - datatoken & metadata
###
FIXME

#allow your algo for C2D for that dataset:
### npm run cli allowAlgo did:op:023E.. did:op:BfAB..
FIXME

#start a compute job
### npm run cli startCompute did:op:02d3.. did:op:BfAB..
FIXME

#get compute job status
### pm run cli getCompute 3a98..
FIXME

#watch the logs & algo output above
FIXME




```

