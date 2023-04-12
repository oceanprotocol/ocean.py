<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Publish & Metadata update Flows for credentials

This quickstart describes how to use credentials in order to limit access to a dataset.

Ensure that you've already (a) [installed Ocean](install.md), and (b) [set up locally](setup-local.md) or [remotely](setup-remote.md).

Here are the steps:

1.  Publish a dataset that can only be accessed by Alice and Bob. Everyone else will be denied.
2.  Update the dataset so only Charlie will be denied, everyone else will have access.


Let's go through each step.

## 2. David publishes the API asset, allowing only Alice and Bob as consumers


```python
url = 'http://www.example.net'
credentials = {
        "allow": [{"type": "address", "values": [alice, bob]}],
        "deny": [],
}
#create asset
(data_nft, datatoken, ddo) = ocean.assets.create_url_asset(name, url, {"from": david},credentials=credentials)
print(f"Just published asset, with did={ddo.did}")
```


That's it! You've created a data asset which is accesible only to Alice and Bob. Consume here is just like in [consume-flow](consume-flow.md). 


## 2. David updates the asset, allowing everyone, but denying Charlie

```python
ddo = ocean.assets.resolve(DID_FROM_PREVIOUS_STEP)
ddo.credentials = {
        "allow": [],
        "deny": [{"type": "address", "values": [charlie]}],
}
ddo = ocean.assets.update(ddo, {"from": david})
```


That's it! Now everyone can access the dataset, except Charlie. Consume here is just like in [consume-flow](consume-flow.md). 

For more information about credentials, you can refer to [docs](https://docs.oceanprotocol.com/core-concepts/did-ddo#credentials).
