<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Publish Flow

This quickstart describes how data is published, including metadata.

Here are the steps:

1.  Setup
2.  Publish Dataset

Let's go through each step.

## 1. Setup

### First steps

From [installation-flow](install.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library
- [x] Setup : Set envvars

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Setup in Python

## 2. Publish Dataset

In the same Python console:
```python
#data info
name = "Branin dataset"
url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"

#create data NFT & datatoken & DDO
(data_NFT, datatoken, ddo) = ocean.assets.create_url_asset(name, url, alice_wallet)
print(f"Just published ddo, with did={ddo.did}")
```

That's it! You've created a data asset of "UrlFile" asset type. It includes a data NFT, a datatoken for the data NFT, and metadata.

## Appendix: Further Flexibility

Here's an example similar to above, but exposes more fine-grained control.

In the same python console:
```python
# Specify metadata and services, using the Branin test dataset
date_created = "2021-12-28T10:55:11Z"
metadata = {
    "created": date_created,
    "updated": date_created,
    "description": "Branin dataset",
    "name": "Branin dataset",
    "type": "dataset",
    "author": "Trent",
    "license": "CC0: PublicDomain",
}

# Use "UrlFile" asset type. (There are other options)
from ocean_lib.structures.file_objects import UrlFile
url_file = UrlFile(
    url="https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"
)

# Publish data asset
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
ddo = ocean.assets.create(
    metadata,
    alice_wallet,
    [url_file],
    datatoken_templates=[1],
    datatoken_names=["Datatoken 1"],
    datatoken_symbols=["DT1"],
    datatoken_minters=[alice_wallet.address],
    datatoken_fee_managers=[alice_wallet.address],
    datatoken_publish_market_order_fee_addresses=[ZERO_ADDRESS],
    datatoken_publish_market_order_fee_tokens=[ocean.OCEAN_address],
    datatoken_publish_market_order_fee_amounts=[0],
    datatoken_bytess=[[b""]],
)
print(f"Just published asset, with did={ddo.did}")
```

### Appendix: Metadata Encryption

The ddo metadata is stored on-chain. It's encrypted and compressed by default. Therefore it supports GDPR "right-to-be-forgotten" compliance rules by default.

You can control this:
- To disable encryption, use `ocean.assets.create(..., encrypt_flag=False)`.
- To disable compression, use `ocean.assets.create(..., compress_flag=False)`.
- To disable both, use `ocean.assets.create(..., encrypt_flag=False, compress_flag=False)`.

### Appendix: Different Templates

`ocean.assets.create(...)` creates a data NFT using ERC721Template, and datatoken using ERC20Template by default. For each, you can use a different template. In creating a datatoken, you can use an existing data NFT by adding the argument `data_nft_address=<data NFT address>`.
