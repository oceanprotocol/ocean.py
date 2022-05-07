<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Key-value database

Data NFTs can store arbitrary key-value pairs on-chain. This opens up their usage for a broad variety of applications, such as comments & ratings, attestations, and privately sharing data (when the value is encrypted).

Let's see how!

Here are the steps:

1. Setup
2. Publish data NFT
3. Add key-value pair to data NFT
4. Retrieve value from data NFT

## 1. Setup

From [datatokens-flow](datatokens-flow.md), do:
- [x] 1. Setup : Prerequisites
- [x] 1. Setup : Download barge and run services
- [x] 1. Setup : Install the library from v4 sources

And:
- [x] 1. Setup : Set envvars

## 2. Publish data NFT

In the console where you set envvars, do the following.

From [datatokens-flow](datatokens-flow.md), do:
- [x] 2.1 Create an ERC721 data NFT

## 3. Add key-value pair to data NFT

```python
key:bytes = b"fav_color"
value:hex = b"blue".hex()
erc721_nft.set_new_data(key, value, alice_wallet)
```

## 4. Retrieve value from data NFT

```python
value2:hex = erc721_nft.get_data(key)
print(f"Found that {key} = {value2}")
```

That's it! Note the simplicity. All data was stored and retrieved from on-chain. We don't need Ocean Provider or Ocean Aquarius for these use cases (though the latter can help for fast querying & retrieval).

We can also encrypt the data. The [personal data NFTs quickstart](READMEs/pdnfts-flow.md) shows an example.

Under the hood, it uses [ERC725](https://erc725alliance.org/), which augments ERC721 with a well-defined way to set and get key-value pairs.
