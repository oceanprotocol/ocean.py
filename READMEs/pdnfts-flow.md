<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Personal data NFTs

Ocean data NFTs can store data encrypted on-chain. Call it a "personal data NFT (PDNFT)" if it's personal data. Here, we show how to leverage PDNFTs to securely share user profile info with dapps.

The basic idea:

- The PDNFT stores data in the NFT, encrypted with a new symmetric key
- To share data to BobDapp, Alice securely shares the symmetric key

Here are the steps:

1. Setup
2. Publish data NFT
3. Add _encrypted_ key-value pair to data NFT
4. Give Dapp permission to view data
5. Dapp retrieves value from data NFT


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

## 3. Add encrypted key-value pair to data NFT

```python
key:bytes = b"fav_color"
value_in:hex = b"blue".hex()
erc721_nft.set_new_data(key, value_in, alice_wallet)
```

## 4. Give Dapp permission to view data

FIXME

## 5. Dapp retrieves value from data NFT

```python
value_out:hex = erc721_nft.get_data(key)
print(f"Found that {key} = {value_out}")
