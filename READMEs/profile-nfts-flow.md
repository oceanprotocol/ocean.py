<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Profile NFTs

This is a flow showing: share user profile data privately with dapps, via Ocean Data NFTs.

Here are the steps:

1. Setup
2. Alice publishes data NFT
3. Alice adds key-value pair to data NFT. 'value' encrypted with symmetric_key
4. Alice gets Dapp's public_key
5. Alice encrypts symmetric_key with Dapp's public key and shares to Dapp
6. Dapp decrypts symmetric_key, then decrypts original 'value'

Key details:
- 
- Public channels may be: (a) writing a new key-value pair on NFT, (b) direct messaging within the browser (c) anything else.

## 1. Setup

From [datatokens-flow](datatokens-flow.md), do:
- [x] 1. Setup : Prerequisites
- [x] 1. Setup : Download barge and run services
- [x] 1. Setup : Install the library from v4 sources

And:
- [x] 1. Setup : Set envvars


## 2. Alice publishes data NFT

In the console where you set envvars, do the following.

From [datatokens-flow](datatokens-flow.md), do:
- [x] 2.1 Create an ERC721 data NFT

## 3. Alice adds key-value pair to data NFT. 'value' encrypted with symmetric_key

```python
from cryptography.fernet import Fernet
from hashlib import sha256
web3 = ocean.web3

field_name:bytes = b"fav_color"
field_val:bytes = b"blue"

symmetric_key = sha256(alice_sign(erc721_nft.address + field_name)) #FIXME

field_val_encr:bytes = encrypt(symmetric_key, field_val)

erc721_nft.set_new_data(field_name, field_val_encr.hex(), alice_wallet)
```

## 4. Alice gets Dapp's public_key

On computing public keys
- If you have the private_key, you can compute the public_key (used below)
- Hardware wallets don't expose private_keys. And, while they do expose a _root_ public_key, you shouldn't publicly share those because it lets anyone see all your wallets
- However, you _can_ compute anyone's public_key from any tx. This is a general solution. Conveniently, Etherscan shows it too.

Then, possible ways for Alice to get Dapp's public key:
- Alice auto-computes from any of Dapp's previous txs.
- Alice retrieves it from a public-ish registry or api, e.g. etherscan
- Dapp computes it from private_key or from past tx, then shares. Sharing could be directly client-side or over a public channel.
  - Client-side could be in a script (used below) or in a browser (typical Dapp).
  - Possible public channels: write a new key-value pair on this NFT; new data NFT for this message; http, email, or any messaging medium
  

```python
# Dapp's wallet
dapp_private_key = os.getenv('TEST_PRIVATE_KEY2')
dapp_wallet = Wallet(ocean.web3, dapp_private_key, config.block_confirmations, config.transaction_timeout)
print(f"dapp_wallet.address = '{dapp_wallet.address}'")
print(f"dapp_wallet.public_key = '{dapp_wallet.public_key}'")

# Now, assume that Alice has Dapp's public_key, eg shared by Dapp
```

## 5. Alice shares symmetric_key to Dapp, encrypted with Dapp's public_key. Public channel ok

```python
#FIXME
from ecies import encrypt, decrypt
```

## 6. Dapp decrypts symmetric_key, then decrypts original value

FIXME
