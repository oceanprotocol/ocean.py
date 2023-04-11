<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->


# Quickstart: Search Assets Flow

This quickstart describes how assets can be found by their `tags` from Aquarius.


## 1. Setup

Ensure that you've already (a) [installed Ocean](install.md), and (b) [set up locally](setup-local.md) or [remotely](setup-remote.md).

## 2. Alice publishes datasets

Now, you're Alice.

```python
#data info
url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"

# Created a list of tags for the following assets
tags = [
    ["Branin dataset 1", "test", "ganache", "best asset"],
    ["Branin dataset 2", "test", "ocean"],
    ["Branin dataset 3", "AI", "dataset", "testing"],
]
# Publish few assets for testing
for tag in tags:
    name = tag[0]
    tx_dict = {"from": alice}
    from ocean_lib.ocean.ocean_assets import OceanAssets
    metadata = ocean.assets.__class__.default_metadata(name, tx_dict)
    metadata.update({"tags": tag[1:]})
    (data_NFT, datatoken, ddo) = ocean.assets.create_url_asset(name, url, tx_dict, metadata=metadata)
    print(f"Just published asset, with did={ddo.did}")
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

## Running custom queries
You can run any custom ES query using OceanAssets. For example:
```python
results = ocean.assets.query(
    {
        "query": {
            "query_string": {
                "query": "Branin dataset 3",
                "fields": ["metadata.name"],
            }
        }
    }
)
assert results[0].metadata["name"] == "Branin dataset 3"
```
