<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Demonstrator: Personal data NFTs (PDNFTs)

Here, we show how Ocean data NFTs can be used as PDNFTs, for securely sharing data with dapps.

The basic idea:

- The PDNFT stores data in the NFT, encrypted with a new symmetric key
- To share data to BobDapp, Alice securely shares the symmetric key

Here are the steps:

1. Setup
2. Alice publishes Data NFT
3. Alice adds data to Data NFT
4. Alice shares PDNFT data to BobDapp
5. BobDapp decrypts and views PDNFT data

## 1. Setup

### First steps

To get started with this guide, please refer to [datatokens-flow](datatokens-flow.md) and complete the following steps :
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library from v4 sources

### Set envvars

Set the required enviroment variables as described in [datatokens-flow](datatokens-flow.md):
- [x] Setup : Set envvars


## 2. Alice Publishes Data NFT

In your project folder (i.e. my_project from `Install the library` step) and in the work console where you set envvars, run the following:

Please refer to [datatokens-flow](datatokens-flow.md) and complete the following steps :
- [x] 2.1 Create an ERC721 data NFT


## 3. Alice adds data to Data NFT

First, play with get & set non-encrypted data
```python
key1:bytes = b"fav_color"
value1_in:hex = b"blue".hex()
erc721_nft.set_new_data(key1, value1_in, alice_wallet)
value1_out:hex = erc721_nft.get_data(key1)
print(f"Found that {key1} = {value1_out}")
```

Now, let's do it encrypted
```python
key2:bytes = b"fav_food"
value2_in:hex = b"jello".hex()
erc721_nft.set_new_data(key2, value2_in, alice_wallet)
value2_out:hex = erc721_nft.get_data(key2)
print(f"Found that {key2} = {value2_out}")
```

## 4. Alice shares PDNFT data to BobDapp

FIXME

## 5. BobDapp decrypts and views PDNFT data

FIXME