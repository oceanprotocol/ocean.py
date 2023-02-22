<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: On-Chain Key-Value Store for Public Sharing

Data NFTs can store arbitrary key-value pairs, to be an on-chain key-value store.

They can be used for:
1. **Publicly sharing AI models** of small to medium size
2. **Publicly sharing AI model predictions**
3. **Comments & ratings in Dapps**
4. **Digital Attestations**, e.g. for verifiable credentials

This flow is appropriate for:
- **Public data**. The next README will explore for private sharing.
- **Small to medium-sized datasets.** For larger datasets, store the data off-chain and share via Ocean datatokens.

Here are the steps:

1. Setup
2. Publish data NFT
3. Add key-value pair to data NFT
4. Retrieve value from data NFT

## 1. Setup

Ensure that you've already (a) [installed Ocean](install.md), and (b) [set up locally](setup-local.md) or [remotely](setup-remote.md).

## 2. Publish data NFT

In Python console:
```python
data_nft = ocean.data_nft_factory.create({"from": alice}, 'NFT1', 'NFT1')
```

## 3. Add key-value pair to data NFT

```python
# Key-value pair
model_key = "my_MLP"
model_value = "<insert MLP weights here>"

# set
data_nft.set_data(model_key, model_value, {"from": alice})
```

## 4. Retrieve value from data NFT

```python
model_value2 = data_nft.get_data(model_key)
print(f"Found that {model_key} = {model_value2}")
```

This data is public, so anyone can retrieve it.

That's it! Note the simplicity. All data was stored and retrieved from on-chain. We don't need Ocean Provider or Ocean Aquarius for these use cases (though the latter can help for fast querying & retrieval).

Under the hood, it uses [ERC725](https://erc725alliance.org/), which augments ERC721 with a well-defined way to set and get key-value pairs.

## 5. Next step

This README showed how to share _public_ key-value data. The next README covers private data. [Let's go there!](key-value-private.md).
