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

### First steps

To get started with this guide, please refer to [datatokens-flow](datatokens-flow.md) and complete the following steps :
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library from v4 sources

### Set envvars

Set the required enviroment variables as described in [datatokens-flow](datatokens-flow.md):
- [x] Setup : Set envvars


## 2. Publish data NFT

In your project folder (i.e. my_project from `Install the library` step) and in the work console where you set envvars, run the following:

Please refer to [datatokens-flow](datatokens-flow.md) and complete the following steps :
- [x] 2.1 Create an ERC721 data NFT

## 3. Add key-value pair to data NFT

```python
key:bytes = b"fav_color"
value_in:hex = b"blue".hex()
erc721_nft.set_new_data(key, value_in, alice_wallet)
```

## 4. Retrieve value from data NFT

```python
value_out:hex = erc721_nft.get_data(key)
print(f"Found that {key} = {value_out}")
```

That's it! Note the simplicity of what just happened. All data was stored and retrieved on-chain. We don't need Ocean Provider or Ocean Aquarius for these use cases (though the latter can help for fast querying & retrieval).

We can also encrypt the data. The [personal data NFTs quickstart](READMEs/pdnfts-flow.md) shows an example.

Under the hood, it uses [ERC725](https://erc725alliance.org/), which augments ERC721 with a well-defined way to set and get key-value pairs.
