<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Private Sharing of On-Chain Data

## Introduction
This quickstart describes how to use Ocean data NFTs to publish data on-chain, then privately share it to multiple parties.

It can be used for:
1. **Sharing AI models** of small to medium size, to specified parties.
2. **Sharing AI model predictions** to specified parties.
3. **["Soulbound Tokens"](https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID4105763_code1186331.pdf?abstractid=4105763&mirid=1)** approach to Web3 identity, where an individual's attributes are fields in one (or more) data NFTs.
4. **Profile NFTs / "Login with Web3"** where a Dapp accesses userdata. In this case, the code would be running in the browser via [pyscript](https://www.pyscript.org); or it would be an equivalent flow using JS not Python. This can be viewed as a special case of (2).

To generalize, this flow is appropriate for:
- **Small to medium-sized datasets.** For larger datasets, store the data off-chain and share via Ocean datatokens.
- **When the data sharer knows (or can compute) the recipient's public key.** When this isn't known - such as for faucets to serve free data to anyone, or for selling priced data to anyone, then use Ocean datatokens.

## Steps

The quickstart follows these steps, for an example of privately sharing an AI model.

Steps by AI modeler (Alice):
1. Setup
2. Publish data NFT
3. Encrypt & store on-chain AI model
4. Share encryption key via chain

Steps by AI model retriever (Bob):
5. Get encryption key via chain
6. Retrieve from chain & decrypt AI model

## 1. Setup

Ensure that you've already (a) [installed Ocean](install.md), and (b) [set up locally](setup-local.md) or [remotely](setup-remote.md).

## 2. Publish data NFT

Here, we publish a data NFT like elsewhere. To make it a soul

bound token (SBT). we set `transferable=False`.

In the Python console:
```python
# Publish an NFT token. Note "transferable=False"
data_nft = ocean.data_nft_factory.create({"from": alice}, 'NFT1', 'NFT1', transferable=False)
```

## 3. Encrypt & store on-chain AI model

Here, we'll symmetrically encrypt an AI model, then store it as a key-value pair in a data NFT on-chain.

In the Python console:
```python
# Key-value pair
model_label = "my_MLP"
model_value = "<insert MLP weights here>"

# Compute a symmetric key: unique to this (nft, nft field) and (your priv key)
# Therefore you can calculate it anytime
from ocean_lib.ocean import crypto
symkey = crypto.calc_symkey(data_nft.address + model_label + alice.private_key)

# Symmetrically encrypt AI model
model_value_symenc = crypto.sym_encrypt(model_value, symkey)

# Save model to chain
data_nft.set_data(model_label, model_value_symenc, {"from": alice})
```

## 4. Share encryption key via chain

There are many possible ways for Alice to share the symkey to Bob. Here, Alice shares it securely on a public channel by encrypting the symkey in a way that only Bob can decrypt:
- The public channel is on the same data NFT, on-chain
- So that only Bob can decrypt: Alice asymetricallys encrypt the symkey with Bob's public key, for Bob to decrypt with his private key.

In the Python console:
```python
# Get Bob's public key. There are various ways; see appendix.
pubkey = crypto.calc_pubkey(bob.private_key)
assert pubkey == str(bob.public_key)

# Asymmetrically encrypt symkey, using Bob's public key
symkey_asymenc = crypto.asym_encrypt(symkey, pubkey)

# Save asymetrically-encrypted symkey to chain
data_nft.set_data("symkey", symkey_asymenc, {"from": alice})
```


## 5. Get encryption key via chain

Whereas the first four steps were done by the AI model sharer (Alice), the remaining steps are done by the AI model receiver (Bob). You're now Bob.

In the Python console:
```python
# Retrieve the asymetrically-encrypted symkey from chain
symkey_asymenc2 = data_nft.get_data("symkey")

# Asymetrically decrypt symkey, with Bob's private key
symkey2 = crypto.asym_decrypt(symkey_asymenc2, bob.private_key)
```

## 6. Retrieve from chain & decrypt AI model

In the Python console:
```python
# Retrieve the symetrically-encrypted model from chain
model_value_symenc2 = data_nft.get_data(model_label)

# Symetrically-decrypt the model, with the symkey retrieved in step 5
model_value2 = crypto.sym_decrypt(model_value_symenc2, symkey2)

print(f"Loaded model {model_label} = {model_value2}")
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


