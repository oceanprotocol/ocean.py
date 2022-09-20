<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Publish Historical ETH Price, from Binance API

This quickstart describes a flow to publish historical ETH price as a data asset, using Binance API.

Here are the steps:

1.  Setup
2.  Alice publishes API data asset

Let's go through each step.

## 1. Setup

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library
- [x] Setup : Set envvars
- [x] Setup : Setup in Python

## 2. Alice Publishes API data asset

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

# we use just a simple graphql query
from ocean_lib.structures.file_objects import GraphqlQuery
graphql_query = GraphqlQuery(
    url="https://v4.subgraph.rinkeby.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph",
    query="""
                    query{
                        nfts(orderBy: createdTimestamp,orderDirection:desc){
                            id
                            symbol
                            createdTimestamp
                        }
                    }
                    """
)

# Publish dataset. It creates the data NFT, datatoken, and fills in metadata.
asset = ocean.assets.create(
    metadata,
    alice_wallet,
    [graphql_query],
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

