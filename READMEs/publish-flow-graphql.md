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
name = "Data ETH price Uniswap hourly"
url = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
query = """query{
    tokenHourDatas(first: 1000, where: {token: "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"}, orderBy: periodStartUnix, orderDirection: desc) {
        periodStartUnix
        priceUSD
        open
        high
        low
        close
        volume
        volumeUSD
    }
}
"""

#create asset
(data_nft, datatoken, asset) = ocean.assets.create_graphql_asset(name, url, query, alice_wallet)
print(f"Just published asset, with did={asset.did}")
```

That's it! You've created a data asset of "GraphqlQuery" asset type. It includes a data NFT, a datatoken for the data NFT, and metadata.

## 3.  Consume dataset

you can consume the asset as shown below. The file downloaded is a .json and stored locally. From that, use the python `json` library to parse it as desired.

```python
to_address = bob_wallet.address
amt_tokens = ocean.to_wei(10)  # just need 1, send more for spare
datatoken.mint(to_address, amt_tokens, alice_wallet)

# Bob sends a datatoken to the service to get access; then downloads
file_name = ocean.assets.download_file(asset.did, bob_wallet)
```