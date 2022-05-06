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

We use 'field_name' not 'key' for key-value pair, to avoid confusion with the encrypt/decrypt symmetric key.

```python
import eth_keys
from ecies import encrypt, decrypt
from hashlib import sha256
web3 = ocean.web3

field_name:bytes = b"fav_color"
field_val = b"blue"

alice_private_key = alice_wallet.private_key.encode("utf-8")

#have a unique private key for each field; only Alice knows all
h:str = sha256(alice_private_key + field_name).hexdigest()
h = h[:32] #first 32 bytes
h:bytes = h.encode("utf-8") 
field_privkey = eth_keys.keys.PrivateKey(h)

field_pubkey = field_privkey.public_key

field_val_encr:bytes = encrypt(field_pubkey.to_hex(), field_val)

erc721_nft.set_new_data(field_name, field_val_encr.hex(), alice_wallet)
```

## 4. Give Dapp permission to view data

FIXME

## 5. Dapp retrieves value from data NFT

```python
value_out:hex = erc721_nft.get_data(field_name)
print(f"Found that {field_name} = {value_out}")
