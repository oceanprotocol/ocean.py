<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Publish & Consume Flow for GraphQL data type

This quickstart describes a flow to publish & consume GraphQL-style URIs. In our example, the data asset is a query to find data NFTs via ocean-subgraph.

Here are the steps:

1.  Setup
2.  Publish dataset
3.  Consume dataset

Let's go through each step.

## 1. Setup

Ensure that you've already (a) [installed Ocean](install.md), and (b) [set up locally](setup-local.md) or [remotely](setup-remote.md).

## 2. Publish dataset

In the same Python console:
```python
#data info
name = "Data NFTs in Ocean"
url="https://v4.subgraph.goerli.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph"
query="""query{
               nfts(orderBy: createdTimestamp,orderDirection:desc){
                    id
                    symbol
                    createdTimestamp
                    }
               }
"""

#create asset
(data_nft, datatoken, ddo) = ocean.assets.create_graphql_asset(name, url, query, {"from": alice})
print(f"Just published asset, with did={ddo.did}")
```

That's it! You've created a data asset of "GraphqlQuery" asset type. It includes a data NFT, a datatoken for the data NFT, and metadata.

## 3.  Consume dataset

Consume here is just like in [consume-flow](consume-flow.md). The file downloaded is a .json. From that, use the python `json` library to parse it as desired.

