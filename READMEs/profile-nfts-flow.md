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
from hashlib import sha256
from eth_account.messages import encode_defunct
sign = ocean.web3.eth.account.sign_message
keccak = ocean.web3.keccak
from base64 import b64encode

#Key-value pair
profiledata_name = "fav_color"
profiledata_val = "blue"

#Prep key for setter. Contract/ERC725 requires keccak256 hash
profiledata_name_hash = keccak(text=profiledata_name)

#Choose a symkey where:
# - sharing it unlocks only this field: make unique to this data nft & field
# - only Alice can compute it: make it a function of her private key
# - is hardware wallet friendly: uses Alice's digital signature not private key
preimage = erc721_nft.address + profiledata_name
msg = encode_defunct(text=sha256(preimage.encode('utf-8')).hexdigest())
signed_msg = sign(msg, private_key=alice_wallet.private_key)
symkey = b64encode(signed_msg.signature.hex().encode('ascii'))[:43] + b'=' #bytes

#Prep value for setter
profiledata_val_encr_hex = Fernet(symkey).encrypt(profiledata_val.encode('utf-8')).hex()

#set
erc721_nft.set_new_data(profiledata_name_hash, profiledata_val_encr_hex, alice_wallet)
```

## 4. Alice gets Dapp's public_key

There are various ways to compute public_key, and for Alice to get it. Here, the Dapp computes public_key from its private_key, then shares with Alice client-side.

```python
from eth_keys import keys
from eth_utils import decode_hex

dapp_private_key = os.getenv('TEST_PRIVATE_KEY2')
dapp_private_key_obj = keys.PrivateKey(decode_hex(dapp_private_key))
dapp_public_key = str(dapp_private_key_obj.public_key) #str
dapp_address = dapp_private_key_obj.public_key.to_address() #str
```

## 5. Alice encrypts symkey with Dapp's public key and shares to Dapp

```python
from ecies import encrypt as asymmetric_encrypt

symkey_name = (profiledata_name + ':for:' + dapp_address[:10]) #str
symkey_name_hash = keccak(text=symkey_name)

symkey_val_encr = asymmetric_encrypt(dapp_public_key, symkey) #bytes
symkey_val_encr_hex = symkey_val_encr.hex() #hex

# arg types: key=bytes32, value=bytes, wallet=wallet
erc721_nft.set_new_data(symkey_name_hash, symkey_val_encr_hex, alice_wallet)
```

## 6. Dapp decrypts symkey, then decrypts original 'value'

```python
from cryptography.fernet import Fernet
from ecies import decrypt as asymmetric_decrypt

#symkey_name, symkey_name_hash = (Dapp would set like above)
symkey_val_encr_hex2 = erc721_nft.get_data(symkey_name_hash)
symkey2 = asymmetric_decrypt(dapp_wallet.private_key, symkey_val_encr_hex2)

profiledata_val_encr_hex2 = erc721_nft.get_data(profiledata_name_hash)
profiledata_val2 = Fernet(symkey).decrypt(profiledata_val_encr_hex2)

print("Dapp found profiledata {profiledata_name} = {profiledata_val2}")
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
  

