<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Publish & Consume Flow for GraphQL data type

This quickstart describes a flow to publish & consume GraphQL-style URIs.

Here are the steps:

1.  Setup
2.  Alice publishes GraphQL-style dataset
3.  Bob consumes the data asset with a GraphQL-shaped query

Let's go through each step.

## 1. Setup

### First steps

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
*NOTE: before starting barge, please type " export PROVIDER_VERSION=graphql"  (will remove this when PR is merged in main provider)
- [x] Setup : Install the library
- [x] Setup : Set envvars
- [x] Setup : Setup in Python

## 2. Alice Publishes GraphQL-style Dataset

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
url_file = GraphqlQuery(
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
    [url_file],
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


3.  Bob consumes the data asset with a GraphQL-shaped query

FIXME
