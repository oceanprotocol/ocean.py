<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Configure Brownie

Here, we configure Brownie, to connect with smart contracts on the chain.

We assume you've already [installed Ocean](install.md).

## 1. About Brownie

ocean.py uses [Brownie](https://eth-brownie.readthedocs.io/en/latest/) to connect with deployed smart contracts.

Brownie was installed as the `eth-brownie` pypi package, when you installed Ocean (`ocean-lib` package).

Thanks to Brownie, ocean.py treats each Ocean smart contract as a Python _class_, and each deployed smart contract as a Python _object_. We love this feature, because it means Python programmers can treat Solidity code as Python code! 🤯

## 2. Brownie Network Configuration

### 2.1 Configuration File

Brownie's network configuration file is at `~/.brownie/network-config.yaml`. It has settings for each network, e.g. development (ganache), Ethereum mainnet, Polygon, and Mumbai.

Each network gets specifications for:
- `host` - the RPC URL, i.e. what URL do we pass through to talk to the chain
- `required_confs` - the number of confirmations before a tx is done 
- `id` - e.g. `polygon-main` (Polygon), `polygon-test` (Mumbai)

[Here's](https://eth-brownie.readthedocs.io/en/v1.6.5/config.html) the `network-config.yaml` from Brownie docs. It can serve as a comparison to your local copy.

`development` chains run locally; `live` chains run remotely.


### 2.2 Config of local networks (ganache)

`network-config.yaml` uses the id `development`.


### 2.3 Config of remote networks

Ocean.py follows the exact `id` name for the network's name from the default brownie configuration file. Therefore, you need to ensure that your target network name matches the corresponding brownie `id`.

**Networks supported.** All the [Ocean-deployed](https://docs.oceanprotocol.com/core-concepts/networks) chains are in `network-config.yaml` default. One exception is Energy Web Chain (EWC). To use EWC, add the following to `network-config.yaml`:
```yaml
- name: energyweb
  networks:
  - chainid: 246
    host: https://rpc.energyweb.org
    id: energyweb
    name: energyweb
```

**RPCs and Infura.** The brownie default RPCs require you to have your own infura account, and corresponding token WEB3_INFURA_PROJECT_ID.

- If you have an infura account: in console, `export WEB3_INFURA_PROJECT_ID=<your infura ID>`
- If not: one way is to get an Infura account. Simpler yet is you can bypass the need for it, by changing to RPCs that don't need tokens. The command below replaces infura RPCs with public RPCs in `network-config.yaml`:

```console
sed -i 's#https://polygon-mainnet.infura.io/v3/$WEB3_INFURA_PROJECT_ID#https://polygon-rpc.com/#g; s#https://polygon-mumbai.infura.io/v3/$WEB3_INFURA_PROJECT_ID#https://rpc-mumbai.maticvigil.com#g' ~/.brownie/network-config.yaml
```



## 3. Next steps

You've now set up Brownie, great!

Next, you can either do [setup locally](setup-local.md), or [remotely](setup-remote.md).

If you're new to this, we recommend to start with local.

