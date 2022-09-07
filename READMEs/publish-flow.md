<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Publish Flow

This quickstart describes how data is published, including metadata.

Here are the steps:

1.  Setup
2.  Alice publishes data asset

Let's go through each step.

## 1. Setup

### First steps

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library from v4 sources
- [x] Setup : Set envvars
- [x] Setup : Setup in Python

## 2. Publish Dataset

Then in the same python console:
```python
from ocean_lib.web3_internal.constants import ZERO_ADDRESS

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

# ocean.py offers multiple file types, but a simple url file should be enough for this example
from ocean_lib.structures.file_objects import UrlFile
url_file = UrlFile(
    url="https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"
)

# Publish dataset. It creates the data NFT, datatoken, and fills in metadata.
asset = ocean.assets.create(
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

did = asset.did  # did contains the datatoken address
print(f"did = '{did}'")
```

In this case, we used the "download" service type. There are other options too.

The asset metadata stored on-chain is encrypted and compressed by default.
It is encouraged that publishers encrypt asset metadata so that the asset supports GDPR "right-to-be-forgotten" compliance rules.

To disable encryption, use `asset = ocean.assets.create(..., encrypt_flag=False)`.
To disable compression, use`asset = ocean.assets.create(..., compress_flag=False)`.
It is possible to disable both encryption and compression, if desired.

`ocean.assets.create(...)` automatically deploys a data NFT token using the ERC20Template. 
If you want to use a different template or reuse a previously deployed data NFT token, 
you can create the data NFT token separately, then use the `data_nft_address=<data NFT address>` 
parameter when calling the create function.
