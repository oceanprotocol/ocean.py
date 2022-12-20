<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Publish & Consume Flow using onchain data source

This quickstart describes a flow to publish & consume onchain data source

Here are the steps:

1.  Setup
2.  Publish dataset
3.  Consume dataset

Let's go through each step.

## 1. Setup

From [installation-flow](install.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library
- [x] Setup : Set envvars

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Setup in Python

## 2. Publish dataset

In the same Python console:
```python
#data info
from ocean_lib.ocean.util import get_address_of_type

name = "swapOceanFee function call"
contract_address = get_address_of_type(config, "Router")
contract_abi = {
                "inputs": [],
                "name": "swapOceanFee",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function",
		}

#create asset
(data_nft, datatoken, ddo) = ocean.assets.create_onchain_asset(name, contract_address, contract_abi, alice)
print(f"Just published asset, with did={ddo.did}")
```

That's it! You've created a data asset of "SmartContractCall" asset type. It includes a data NFT, a datatoken for the data NFT, and metadata.

## 3.  Consume the dataset

(Consume here is just like in [consume-flow](READMEs/consume-flow.md]. The file downloaded is a .json. From that, use the python `json` library to parse it as desired.)
