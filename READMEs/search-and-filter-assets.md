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

From [installation-flow](install.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library
- [x] Setup : Set envvars

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do:
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
    (data_NFT, datatoken, ddo) = ocean.assets.create_url_asset(name, url, alice_wallet)
    print(f"Just published asset, with did={ddo.did}")
    
    # Update the metadata introducing `tags`
    ddo.metadata.update({"tags": tag})
    ddo = ocean.assets.update(asset=ddo, publisher_wallet=alice_wallet, provider_uri=config["PROVIDER_URL"])
    print(f"Just updated the metadata of the asset with did={ddo.did}.")

```
## 3. Alice filters assets by their `tags`

Alice can filter the assets by a certain tag and after can retrieve the necessary
information afterwards.

```python
# Get a list of assets filtered by a given tag.
# All assets that contain the specified tag name
tag = "test"
all_ddos = ocean.assets.search(tag)

# Filter just by the `tags` key
filtered_ddos = list(
    filter(
        lambda a: tag in a.metadata["tags"],
        list(filter(lambda a: "tags" in a.metadata.keys(), all_ddos)),
    )
)

# Make sure that the provided tag is valid.
assert len(filtered_ddos) > 0, "Assets not found with this tag."

# Retrieve the wanted information from assets.
for ddo in filtered_ddos:
    print(f"ddo.did :{ddo.did}")
    print(f"ddo.metadata :{ddo.metadata}")
    print(f"ddo.nft :{ddo.nft}")
    print(f"ddo.datatokens :{ddo.datatokens}")
```