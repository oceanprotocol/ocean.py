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
import eth_keys
from ecies import encrypt, decrypt
from hashlib import sha256
web3 = ocean.web3

field_name:bytes = b"fav_color"
field_val:bytes = b"blue"

alice_private_key = alice_wallet.private_key.encode("utf-8")

#have a unique private key for each field; only Alice knows all
h:str = sha256(alice_private_key + field_name).hexdigest()[:32]
h:bytes = h.encode("utf-8") 
field_privkey = eth_keys.keys.PrivateKey(h)

field_pubkey = field_privkey.public_key

field_val_encr:bytes = encrypt(field_pubkey.to_hex(), field_val)

erc721_nft.set_new_data(field_name, field_val_encr.hex(), alice_wallet)
```

Note: We used 'field_name' not 'key' for key-value pair, to avoid confusion with the encrypt/decrypt symmetric key.

## 4. Give Dapp permission to view data

The Dapp has permission if "fav_color:can_access:<Dapp_addr>" is True. To set this key/value pair, the Dapp creates the tx, gets Alice to sign it, then sends it off.

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

# Dapp creates a tx requesting access, that Alice signs
field2_name:bytes = f"fav_color:can_access:{dapp_wallet.address}".encode("utf-8")
field2_val:hex = b"True".hex()

raw_tx = erc721_nft.set_new_data(
  "setNewData", (field2_name, field2_val, {"do_sign_and_send": False}))

# Dapp gets Alice to sign
signed_tx = alice_wallet.sign_tx(raw_tx)

# Dapp sends off tx, waits until done
tx_hash = web3.eth.send_raw_transaction(signed_tx) 
chain_id = get_chain_id(web3)
wait_for_transaction_receipt_and_block_confirmations(
  web3, tx_hash, block_confirmations,
  block_number_poll_interval, transaction_timeout)

# Now, the Dapp officially has permission!
```

## 5. Dapp retrieves value from data NFT

```python
field_val_encr2:hex = erc721_nft.get_data(field_name)
print(f"Found that {field_name} = {value_out}")
```