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

To get started with this guide, please refer to [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md) and complete the following steps :
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library from v4 sources
- [x] Setup : Set envvars

In your project folder (i.e. my_project from `Install the library` step) and in the work console where you set envvars, run the following:

Please refer to [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md) and complete the following steps :
- [x] 2.1 Create an ERC721 data NFT

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

# Encrypt file(s) using provider
encrypted_files = ocean.assets.encrypt_files([url_file])


# Publish asset with services on-chain.
# The download (access service) is automatically created, but you can explore other options as well
asset = ocean.assets.create(
    metadata,
    alice_wallet,
    encrypted_files,
    erc20_templates=[1],
    erc20_names=["Datatoken 1"],
    erc20_symbols=["DT1"],
    erc20_minters=[alice_wallet.address],
    erc20_fee_managers=[alice_wallet.address],
    erc20_publish_market_order_fee_addresses=[ZERO_ADDRESS],
    erc20_publish_market_order_fee_tokens=[ocean.OCEAN_address],
    erc20_caps=[ocean.to_wei(100000)],
    erc20_publish_market_order_fee_amounts=[0],
    erc20_bytess=[[b""]],
)

did = asset.did  # did contains the datatoken address
print(f"did = '{did}'")

```

Note on asset encryption: In order to encrypt the entire asset, when using a private market or metadata cache, use the encrypt keyword.
Same for compression and you can use a combination of the two. E.g:
`asset = ocean.assets.create(..., encrypt_flag=True)` or `asset = ocean.assets.create(..., compress_flag=True)`
