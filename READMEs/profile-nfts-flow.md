<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Profile NFTs

This is a flow showing: share user profile data privately with dapps, via Ocean Data NFTs.

Here are the steps:

1. Setup
2. Alice publishes data NFT
3. Alice adds key-value pair to data NFT. 'value' encrypted with a symmetric key 'symkey'
4. Alice gets Dapp's public_key
5. Alice encrypts symkey with Dapp's public key and shares to Dapp
6. Dapp decrypts symkey, then decrypts original 'value'

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

## 3. Alice adds key-value pair to data NFT. 'value' encrypted with a symmetric key 'symkey'

```python
#imports
from cryptography.fernet import Fernet
from hashlib import sha256 as hash
from eth_account.messages import encode_defunct
sign = ocean.web3.eth.account.sign_message
from base64 import b64encode

#Key-value pair, with value in plaintext
profiledata_name:bytes = b"fav_color"
profiledata_val:bytes = b"blue"

#Choose a symkey that:
# - only Alice can compute: a function of her private key
# - is hardware wallet friendly: uses Alice's digital signature not priv. key
# - sharing it unlocks only this field: make unique to this data nft & field
nft_addr = erc721_nft.address.encode('utf-8')
msg = encode_defunct(text=hash(nft_addr + profiledata_name).hexdigest())
signed_msg = sign(msg, private_key=alice_wallet.private_key)
symkey = b64encode(signed_msg.signature.hex().encode('ascii'))[:43] + b'='

#Symmetrically encrypt, and store it
profiledata_val_encr:bytes = Fernet(symkey).encrypt(profiledata_val)
erc721_nft.set_new_data(profiledata_name, profiledata_val_encr.hex(), alice_wallet)
```

## 4. Alice gets Dapp's public_key

There are various ways to compute public_key, and for Alice to get it. Here, the Dapp computes public_key from its private_key, then shares with Alice client-side.

```python
from eth_keys import keys
from eth_utils import decode_hex

dapp_private_key = os.getenv('TEST_PRIVATE_KEY2')
dapp_public_key = str(keys.PrivateKey(decode_hex(dapp_private_key)).public_key)
```

## 5. Alice encrypts symkey with Dapp's public key and shares to Dapp

```python
from ecies import encrypt as asymmetric_encrypt
web3 = ocean.web3

symkey_name = (profiledata_name.decode('utf-8') + ':for:' + dapp_wallet.address[:10]) #str
symkey_val_encr = str(asymmetric_encrypt(dapp_public_key, symkey)) #str

# arg types: key=bytes32, value=bytes, wallet=wallet
erc721_nft.set_new_data(symkey_name.encode('utf-8'), symkey_val_encr.encode('utf-8'), alice_wallet)
```

## 6. Dapp decrypts symkey, then decrypts original 'value'

```python
from cryptography.fernet import Fernet
from ecies import decrypt as asymmetric_decrypt

#symkey_name = (Dapp would set it like above)
symkey_val_encr = erc721_nft.get_data(symkey_name)
symkey = asymmetric_decrypt(dapp_wallet.private_key, symkey_val_encr)

profiledata_val_encr = erc721_nft.get_data(profiledata_name)
profiledata_val = Fernet(symkey).decrypt(profiledata_val_encr) #symmetric
```


## Appendix

Step 4 mentioned various ways to compute public_key and for Alice to get it. Here are more options.

On computing public keys:
- If you have the private_key, you can compute the public_key (used above)
- Hardware wallets don't expose private_keys. And, while they do expose a _root_ public_key, you shouldn't publicly share those because it lets anyone see all your wallets
- However, you _can_ compute anyone's public_key from any tx. This is a general solution. Conveniently, Etherscan shows it too.

Then, possible ways for Alice to get Dapp's public key:
- Alice auto-computes from any of Dapp's previous txs.
- Alice retrieves it from a public-ish registry or api, e.g. etherscan
- Dapp computes it from private_key or from past tx, then shares. Sharing could be directly client-side or over a public channel.
  - Client-side could be in a script (used above) or in a browser (typical Dapp).
  - Possible public channels: write a new key-value pair on this NFT; new data NFT for this message; http, email, or any messaging medium
  

