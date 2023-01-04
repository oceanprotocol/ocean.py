<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Key-value database

Data NFTs can store arbitrary key-value pairs on-chain. This opens up their usage for a broad variety of applications, such as comments & ratings, attestations, and privately sharing data (when the value is encrypted).

Let's see how!

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
from ocean_lib.models.data_nft import DataNFTArguments
data_nft = ocean.data_nft_factory.create(DataNFTArguments('NFT1', 'NFT1'), {"from": alice})
```

## 3. Add key-value pair to data NFT

```python
# Key-value pair
key = "fav_color"
value = b"blue"

# prep key for setter
from web3.main import Web3
key_hash = Web3.keccak(text=key)  # Contract/ERC725 requires keccak256 hash

# set
data_nft.setNewData(key_hash, value, {"from": alice})
```

## 4. Retrieve value from data NFT

```python
value2_hex = data_nft.getData(key_hash)
value2 = value2_hex.decode('ascii')
print(f"Found that {key} = {value2}")
```

That's it! Note the simplicity. All data was stored and retrieved from on-chain. We don't need Ocean Provider or Ocean Aquarius for these use cases (though the latter can help for fast querying & retrieval).

We can also encrypt the data. Other quickstarts explore this.

Under the hood, it uses [ERC725](https://erc725alliance.org/), which augments ERC721 with a well-defined way to set and get key-value pairs.
