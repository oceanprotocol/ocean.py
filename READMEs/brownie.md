<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Configure Brownie

Here, we configure Brownie.

We assume you've already installed Ocean.

## About Brownie

ocean.py uses [Brownie](https://eth-brownie.readthedocs.io/en/latest/) to connect with deployed smart contracts.

Brownie was installed as the `eth-brownie` pypi package, when you installed Ocean (`ocean-lib` package).

Thanks to Brownie, ocean.py treats each Ocean smart contract as a Python _class_, and each deployed smart contract as a Python _object_. We love this feature, because it means Python programmers can treat Solidity code as Python code!

## Brownie Network Configuration

Brownie's network configuration file is at `~/.brownie/network-config.yaml`. Please review it to ensure that you've set RPC URLs, gas prices, etc according to your preferences.

#### Config of local networks (ganache)

`network-config.yaml` uses the label  "`development`".

#### Config of remote networks

Ocean.py follows the exact `id` name for the network's name from the default brownie configuration file. Therefore, you need to ensure that your target network name matches the corresponding brownie `id`.

`network-config.yaml` default includes all [Ocean-deployed](https://docs.oceanprotocol.com/core-concepts/networks) chains. One exception is Energy Web Chain (EWC). To use EWC, add the following to `network-config.yaml`:
```yaml
- name: energyweb
  networks:
  - chainid: 246
    host: https://rpc.energyweb.org
    id: energyweb
    name: energyweb
```

#### Sample

Here's a sample `network-config.yaml` from brownie docs: https://eth-brownie.readthedocs.io/en/v1.6.5/config.html.


## Next steps

You've now set up Brownie, great!

Next, you can either do [setup locally](setup-local.md), or [remotely](setup-remote.md).

If you're new to this, we recommend to start with local.

