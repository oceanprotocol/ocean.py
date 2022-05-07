<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Personal data NFTs

Ocean data NFTs can store data encrypted on-chain. Call it a "personal data NFT (PDNFT)" if it's personal data. Here, we show how to leverage PDNFTs to securely share user profile info with dapps.

Here are the steps:

1. Setup
2. Alice publishes data NFT
3. Alice adds key-value pair to data NFT. Encrypt value with symmetric_key
4. Dapp requests access and shares public_key. Public channel ok.
5. Alice shares symmetric_key to Dapp, encrypted with Dapp's public_key. Public channel ok.
6. Dapp decrypts symmetric_key, then decrypts original value

Key details:

- Alice can reconstruct symmetric_key anytime via digitally signing. (Therefore works with HW wallets.)
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

## 3. Alice adds key-value pair to data NFT. Encrypt value with symmetric_key

```python
import eth_keys
from ecies import encrypt, decrypt
from hashlib import sha256
web3 = ocean.web3

field_name:bytes = b"fav_color"
field_val:bytes = b"blue"

symmetric_key = alice_sign(erc721_nft.address + field_name) #FIXME

field_val_encr:bytes = encrypt(symmetric_key, field_val)

erc721_nft.set_new_data(field_name, field_val_encr.hex(), alice_wallet)
```

## 4. Dapp requests access and provides public_key. Public channel ok

```python
# setup
from ocean_lib.web3_internal.web3_overrides.utils import \
    wait_for_transaction_receipt_and_block_confirmations
chain_id = get_chain_id(web3)
block_number_poll_interval = BLOCK_NUMBER_POLL_INTERVAL[chain_id]

# Dapp's wallet
dapp_private_key = os.getenv('TEST_PRIVATE_KEY2')
dapp_wallet = Wallet(ocean.web3, dapp_private_key, config.block_confirmations, config.transaction_timeout)
print(f"dapp_wallet.address = '{dapp_wallet.address}'")
print(f"dapp_wallet.public_key = '{dapp_wallet.public_key}'")

# Assume here that Dapp has sent Alice the public_key via public channel
```

## 5. Alice shares symmetric_key to Dapp, encrypted with Dapp's public_key. Public channel ok

FIXME

## 6. Dapp decrypts symmetric_key, then decrypts original value

FIXME
