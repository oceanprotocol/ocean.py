<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Publish & Consume Flow for GraphQL data type

This quickstart describes a flow to publish & consume GraphQL-style URIs. In our example, the data asset is a query to get the daily aggregated data from the ETH/USDC pool in Uniswap V2.

Here are the steps:

1.  Setup
2.  Publish dataset
3.  Consume dataset

Let's go through each step.

## 1. Setup

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library
- [x] Setup : Set envvars
- [x] Setup : Setup in Python

## 2. Publish dataset

In the same Python console:
```python
#data info
name = "Data ETH/USDC"
url="https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"
query="""query{
     pairDayDatas(first: 1000, orderBy: date, orderDirection: asc,
     where: {
          pairAddress: "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc",
          date_gt: 1592505859
     }
     ) {
          date
          reserve0
          reserve1
          dailyVolumeToken0
          dailyVolumeToken1
          dailyVolumeUSD
          reserveUSD
     }
}

"""

#create asset
(data_nft, datatoken, asset) = ocean.assets.create_graphql_asset(name, url, query, alice_wallet)
print(f"Just published asset, with did={asset.did}")
```

That's it! You've created a data asset of "GraphqlQuery" asset type. It includes a data NFT, a datatoken for the data NFT, and metadata.

## 3.  Consume dataset

Consume here is just like in [consume-flow](consume-flow.md). The file downloaded is a .json. From that, use the python `json` library to parse it as desired.

