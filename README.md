<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

[![banner](https://raw.githubusercontent.com/oceanprotocol/art/master/github/repo-banner%402x.png)](https://oceanprotocol.com)

<h1 align="center">ocean.py</h1>

> Python library to privately & securely publish, exchange, and consume data.

<center>

[![Maintainability](https://api.codeclimate.com/v1/badges/a0be65f412a35440c63e/maintainability)](https://codeclimate.com/github/oceanprotocol/ocean.py/maintainability)

</center>

<center>

[![Test Coverage](https://api.codeclimate.com/v1/badges/a0be65f412a35440c63e/test_coverage)](https://codeclimate.com/github/oceanprotocol/ocean.py/test_coverage)

</center>

With ocean.py, you can:

- **Publish** data services: downloadable files or compute-to-data.
  Ocean creates a new [ERC20](https://github.com/ethereum/EIPs/blob/7f4f0377730f5fc266824084188cc17cf246932e/EIPS/eip-20.md)
  datatoken for each dataset / data service.
- **Mint** datatokens for the service
- **Sell** datatokens via an OCEAN-datatoken Balancer pool (for auto price discovery), or for a fixed price
- **Stake** OCEAN on datatoken pools
- **Consume** datatokens, to access the service
- **Transfer** datatokens to another owner, and **all other ERC20 actions**
  using [web3.py](https://web3py.readthedocs.io/en/stable/examples.html#working-with-an-erc20-token-contract) etc.

ocean.py is part of the [Ocean Protocol](https://www.oceanprotocol.com) toolset.

This is in beta state and you can expect running into problems. If you run into them, please open up a [new issue](/issues).

- [🏗 Installation](#-installation)
- [🏄 Quickstart](#-quickstart): simple flow, marketplace, compute-to-data, more
- [🦑 Development](#-development)
- [🏛 License](#-license)

## 🏗 Installation

```console
#Install the ocean.py library. Install wheel first to avoid errors.
pip install wheel
pip install ocean-lib
```
⚠️ For Mac users, if you encounter an issue with "Unsupported Architecture", see [this issue](https://github.com/oceanprotocol/ocean.py/issues/486) for an explanation and run the installation command with ARCHFLAGS set, like so:

`ARCHFLAGS="-arch x86_64" pip install ocean-lib`

## 🏄 Quickstart

Here are flows to try out, from simple to specific detailed variants.

- **[Simple flow](READMEs/datatokens-flow.md)** - the essence of Ocean - creating a data NFT & datatoken.
- **[Marketplace flow](READMEs/marketplace-flow.md)** - a data asset is posted for sale in a datatoken pool, then purchased. Includes metadata.
- **[Fixed rate exchange flow](READMEs/fixed-rate-exchange-flow.md)** - a data asset is posted for sale at fixed rate, then purchased. 
- **[Compute-to-data flow](READMEs/c2d-flow.md)** - uses C2D to build an AI model a dataset that never leaves the premises.

### Learn more

- [Get test OCEAN](READMEs/get-test-OCEAN.md) - from rinkeby
- [Understand config parameters](READMEs/parameters.md) - envvars vs files
- [Learn about off-chain services](READMEs/services.md) - Ocean Provider for data services, Aquarius metadata store
- [Learn about wallets](READMEs/wallets.md) - on generating, storing, and accessing private keys
- [Get an overview of ocean.py](READMEs/overview.md) - key modules and functions

## 🦑 Development

[Go to developers flow](READMEs/developers.md) if you want to further develop ocean.py.

## 🏛 License

    Copyright ((C)) 2022 Ocean Protocol Foundation

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
