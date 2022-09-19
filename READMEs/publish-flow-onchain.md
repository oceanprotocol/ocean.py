<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Publish & Consume Flow using onchain data source

This quickstart describes a flow to publish & consume onchain data source

Here are the steps:

1.  Setup
2.  Alice publishes dataset
3.  Bob consumes the data asset

Let's go through each step.

## 1. Setup

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library
- [x] Setup : Set envvars
- [x] Setup : Setup in Python

## 2. Alice Publishes Dataset with on-chain data

Then in the same python console:
```python
from ocean_lib.web3_internal.constants import ZERO_ADDRESS

# Specify metadata and services, using the Branin test dataset
date_created = "2021-12-28T10:55:11Z"

metadata = {
    "created": date_created,
    "updated": date_created,
    "description": "Branin dataset",
    "name": "Branin dataset",
    "type": "dataset",
    "author": "Trent",
    "license": "CC0: PublicDomain",
}

# we will use our FactoryRouter contract and call "swapOceanFee" function
 abi = {
        "inputs": [],
        "name": "swapOceanFee",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
    router_address = get_address_of_type(
                config, FactoryRouter.CONTRACT_NAME
            )
    onchain_data = SmartContractCall(address=router_address, chainId=web3.eth.chain_id, abi=abi)
    

    

# Publish dataset. It creates the data NFT, datatoken, and fills in metadata.
asset = ocean.assets.create(
    metadata,
    alice_wallet,
    [onchain_data],
    datatoken_templates=[1],
    datatoken_names=["Datatoken 1"],
    datatoken_symbols=["DT1"],
    datatoken_minters=[alice_wallet.address],
    datatoken_fee_managers=[alice_wallet.address],
    datatoken_publish_market_order_fee_addresses=[ZERO_ADDRESS],
    datatoken_publish_market_order_fee_tokens=[ocean.OCEAN_address],
    datatoken_publish_market_order_fee_amounts=[0],
    datatoken_bytess=[[b""]],
)

did = asset.did  # did contains the datatoken address
print(f"did = '{did}'")
```


## 3.  Bob consumes the dataset

(Consume here is just like in [consume-flow](READMEs/consume-flow.md]. The file downloaded is a .json. From that, use the python `json` library to parse it as desired.)

