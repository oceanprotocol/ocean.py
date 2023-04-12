<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Publish & Metadata update Flows for credentials

This quickstart describes how to use credentials in order to limit access to a dataset.

Ensure that you've already (a) [installed Ocean](install.md), and (b) [set up locally](setup-local.md) or [remotely](setup-remote.md).

Here are the steps:

1.  Publish a dataset that can only be accessed by Alice and Bob. Everyone else will be denied.
2.  Update the dataset so only Carlos will be denied, everyone else will have access.


Let's go through each step.

## 2. Carlos publishes the API asset, allowing only Alice and Bob as consumers


```python
url = 'http://www.example.net'
name = "Restricted dataset"
credentials = {
        "allow": [{"type": "address", "values": [alice.address, bob.address]}],
        "deny": [],
}
#create asset
(data_nft, datatoken, ddo) = ocean.assets.create_url_asset(name, url, {"from": carlos}, credentials = credentials)
print(f"Just published asset, with did={ddo.did}")
```


That's it! You've created a data asset which is accesible only to Alice and Bob. Consume here is just like in [consume-flow](consume-flow.md). 


## 2. David updates the asset, allowing everyone, but denying Bob

```python
ddo2 = ocean.assets.resolve(ddo.did)
ddo2.credentials = {
        "allow": [],
        "deny": [{"type": "address", "values": [bob.address]}],
}
ddo2 = ocean.assets.update(ddo2, {"from": carlos})
```


That's it! Now everyone can access the dataset, except Bob. Consume here is just like in [consume-flow](consume-flow.md). 

For more information about credentials, you can refer to [docs](https://docs.oceanprotocol.com/core-concepts/did-ddo#credentials).
