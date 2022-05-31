<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Profile NFTs

This is a flow showing how to do "login with Web3" with the help of Ocean data NFTs. In this flow, a dapp is not only connected to the user's wallet, but it can access profile data that the user has privately shared to it.

Here are the steps:

1. Setup
2. Alice publishes data NFT
3. Alice adds key-value pair to data NFT. 'value' encrypted with a symmetric key 'symkey'
4. Alice gets Dapp's public_key
5. Alice encrypts symkey with Dapp's public key and shares to Dapp
6. Dapp gets & decrypts symkey, then gets & decrypts original 'value'

## 1. Setup

From the [Simple Flow](data-nfts-and-datatokens-flow.md), do:
- [x] 1. Setup : Prerequisites
- [x] 1. Setup : Download barge and run services
- [x] 1. Setup : Install the library from v4 sources

And:
- [x] 1. Setup : Set envvars

## 2. Alice publishes data NFT

We create a data NFT like in Simple Flow, except we set `transferable=False` (and skip print statements).

In the terminal where you set envvars:

```console
python
```

In the Python console:
```python
from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.ocean import Ocean
config = ExampleConfig.get_config()
ocean = Ocean(config)

# Create Alice's wallet
import os
from ocean_lib.web3_internal.wallet import Wallet
alice_private_key = os.getenv('TEST_PRIVATE_KEY1')
alice_wallet = Wallet(ocean.web3, alice_private_key, config.block_confirmations, config.transaction_timeout)

# Publish an NFT token. Note "transferable=False"
data_nft = ocean.create_data_nft('NFTToken1', 'NFT1', alice_wallet, transferable=False)
```

## 3. Alice adds key-value pair to data NFT. 'value' encrypted with a symmetric key 'symkey'

```python
# imports
from base64 import b64encode
from cryptography.fernet import Fernet
from eth_account.messages import encode_defunct
from hashlib import sha256
web3 = ocean.web3

# Key-value pair
profiledata_name = "fav_color"
profiledata_val = "blue"

# Prep key for setter. Contract/ERC725 requires keccak256 hash
profiledata_name_hash = web3.keccak(text=profiledata_name)

# Choose a symkey where:
# - sharing it unlocks only this field: make unique to this data nft & field
# - only Alice can compute it: make it a function of her private key
# - is hardware wallet friendly: uses Alice's digital signature not private key
preimage = data_nft.address + profiledata_name
msg = encode_defunct(text=sha256(preimage.encode('utf-8')).hexdigest())
signed_msg = web3.eth.account.sign_message(msg, private_key=alice_wallet.private_key)
symkey = b64encode(signed_msg.signature.hex().encode('ascii'))[:43] + b'='  # bytes

# Prep value for setter
profiledata_val_encr_hex = Fernet(symkey).encrypt(profiledata_val.encode('utf-8')).hex()

# set
data_nft.set_new_data(profiledata_name_hash, profiledata_val_encr_hex, alice_wallet)
```

## 4. Alice gets Dapp's public_key

There are various ways to compute public_key, and for Alice to get it (see Appendix). Here, the Dapp computes public_key from its private_key, then shares with Alice client-side within the script.

```python
from eth_keys import keys
from eth_utils import decode_hex

dapp_private_key = os.getenv('TEST_PRIVATE_KEY2')
dapp_private_key_obj = keys.PrivateKey(decode_hex(dapp_private_key))
dapp_public_key = str(dapp_private_key_obj.public_key)  # str
dapp_address = dapp_private_key_obj.public_key.to_address()  # str
```

## 5. Alice encrypts symkey with Dapp's public key and shares to Dapp

There are various ways for Alice to share the encrypted symkey to the Dapp (see Appendix). Here, Alice writes a new key-value pair on the same data NFT. This approach allows the Dapp to access the info in future sessions without extra work.

```python
from ecies import encrypt as asymmetric_encrypt

symkey_name = (profiledata_name + ':for:' + dapp_address[:10])  # str
symkey_name_hash = web3.keccak(text=symkey_name)

symkey_val_encr = asymmetric_encrypt(dapp_public_key, symkey)  # bytes

symkey_val_encr_hex = symkey_val_encr.hex()  # hex

# arg types: key=bytes32, value=bytes, wallet=wallet
data_nft.set_new_data(symkey_name_hash, symkey_val_encr_hex, alice_wallet)
```

## 6. Dapp gets & decrypts symkey, then gets & decrypts original 'value'

```python
from ecies import decrypt as asymmetric_decrypt

# symkey_name_hash = <Dapp would set like above>
symkey_val_encr2 = data_nft.get_data(symkey_name_hash)
symkey2 = asymmetric_decrypt(dapp_private_key, symkey_val_encr2)

# profiledata_name_hash = <Dapp would set like above>
profiledata_val_encr_hex2 = data_nft.get_data(profiledata_name_hash)
profiledata_val2_bytes = Fernet(symkey).decrypt(profiledata_val_encr_hex2)
profiledata_val2 = profiledata_val2_bytes.decode('utf-8')

print(f"Dapp found profiledata {profiledata_name} = {profiledata_val2}")
```


## Appendix

Step 4 gave one way for Alice to get the Dapp's public key; step 5 gave one way for the Dapp to get the encrypted symkey. Here are more options.

On computing public keys:
- If you have the private_key, you can compute the public_key (used above)
- Hardware wallets don't expose private_keys. And, while they do expose a _root_ public_key, you shouldn't publicly share those because it lets anyone see all your wallets
- However, you _can_ compute anyone's public_key from any tx. This is a general solution. Conveniently, Etherscan shows it too.

Possible ways for Alice to get Dapp's public key:
- Alice auto-computes from any of Dapp's previous txs.
- Alice retrieves it from a public-ish registry or api, e.g. etherscan
- Dapp computes it from private_key or from past tx, then shares.

Possible ways for Alice to share an encrypted symkey, or for Dapp to share public_key:
- Directly client-side
  - Client-side: in a browser with Metamask - [example by FELToken](https://betterprogramming.pub/exchanging-encrypted-data-on-blockchain-using-metamask-a2e65a9a896c). This is a good choice because it does no on-chain txs.
  - Client-side: in a script. Like done in step 4 above for public key
- Over a public channel:
  - Public channel: write a new key-value pair on the same data NFT. Like done in step 5 above for encrypted symkey. This is a good choice because the Dapp can access the info in future sessions without extra work.
  - Public channel: a new data NFT for each message
  - Public channel: traditional: http, email, or any messaging medium


