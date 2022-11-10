<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->


# Quickstart: Search Assets Flow

This quickstart describes how assets can be found by their `tags` from Aquarius.


Here are the steps:

1.  Setup
2.  Alice creates few assets for testing
3.  Alice searches & filters assets by their `tags`

Let's go through each step.

## 1. Setup

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library
- [x] Setup : Set envvars
- [x] Setup : Setup in Python


## 2. Alice publishes datasets

Now, you're Alice. Using [publish-flow](publish-flow.md) model, do:

```python
import time

from ocean_lib.structures.file_objects import UrlFile
from ocean_lib.web3_internal.constants import ZERO_ADDRESS

# Created a list of tags for the following assets
tags = [
    ["test", "ganache", "best asset"],
    ["test", "ocean"],
    ["AI", "dataset", "testing"],
]
# Publish few assets for testing
date_created = "2021-12-28T10:55:11Z"
for i in range(len(tags)):

    metadata = {
        "created": date_created,
        "updated": date_created,
        "description": "Branin dataset",
        "name": "Branin dataset",
        "type": "dataset",
        "author": "Trent",
        "license": "CC0: PublicDomain",
        "tags": tags[i]
    }

    url_file = UrlFile(
        url="https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"
    )

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
    
    print(f"Just published asset, with did={asset.did}")

# The changes take time to settle
time.sleep(5)

```
## 3. Alice filters assets by their `tags`

Alice can filter the assets by a certain tag and after can retrieve the necessary
information afterwards.

```python
# Get a list of assets filtered by a given tag.
filtered_assets = ocean.search_asset_by_tag(tag='test')

# Make sure that the provided tag is valid.
assert len(filtered_assets) > 0, "Assets not found with this tag."

# Retrieve the wanted information from assets.
for asset in filtered_assets:
    print(f"asset.did :{asset.did}")
    print(f"asset.metadata :{asset.metadata}")
    print(f"asset.nft :{asset.nft}")
    print(f"asset.datatokens :{asset.datatokens}")
```