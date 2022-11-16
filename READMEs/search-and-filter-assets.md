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
#data info
name = "Branin dataset"
url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"

# Created a list of tags for the following assets
tags = [
    ["test", "ganache", "best asset"],
    ["test", "ocean"],
    ["AI", "dataset", "testing"],
]
# Publish few assets for testing
for tag in tags:
    (data_NFT, datatoken, asset) = ocean.assets.create_url_asset(name, url, alice_wallet)
    print(f"Just published asset, with did={asset.did}")
    
    # Update the metadata introducing `tags`
    asset.metadata.update({"tags": tag})
    asset = ocean.assets.update(asset=asset, publisher_wallet=alice_wallet, provider_uri=config["PROVIDER_URL"])
    print(f"Just updated the metadata of the asset with did={asset.did}.")

```
## 3. Alice filters assets by their `tags`

Alice can filter the assets by a certain tag and after can retrieve the necessary
information afterwards.

```python
# Get a list of assets filtered by a given tag.
# All assets that contain the specified tag name
tag = "test"
all_assets = ocean.assets.search(tag)

# Filter just by the `tags` key
filtered_assets = list(
    filter(
        lambda a: tag in a.metadata["tags"],
        list(filter(lambda a: "tags" in a.metadata.keys(), all_assets)),
    )
)

# Make sure that the provided tag is valid.
assert len(filtered_assets) > 0, "Assets not found with this tag."

# Retrieve the wanted information from assets.
for asset in filtered_assets:
    print(f"asset.did :{asset.did}")
    print(f"asset.metadata :{asset.metadata}")
    print(f"asset.nft :{asset.nft}")
    print(f"asset.datatokens :{asset.datatokens}")
```