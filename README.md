<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

[![banner](https://raw.githubusercontent.com/oceanprotocol/art/master/github/repo-banner%402x.png)](https://oceanprotocol.com)

<h1 align="center">ocean.py</h1>

> Python library to privately & securely publish, exchange, and consume data.

[![Maintainability](https://api.codeclimate.com/v1/badges/a0be65f412a35440c63e/maintainability)](https://codeclimate.com/github/oceanprotocol/ocean.py/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/a0be65f412a35440c63e/test_coverage)](https://codeclimate.com/github/oceanprotocol/ocean.py/test_coverage)

With ocean.py, you can:

- **Publish** data services: downloadable files or compute-to-data. Create an ERC721 **data NFT** for each service, and ERC20 **datatoken** for access (1.0 datatokens to access).
- **Sell** datatokens via for a fixed price. Sell data NFTs.
- **Transfer** data NFTs & datatokens to another owner, and **all other ERC721 & ERC20 actions** using [web3.py](https://web3py.readthedocs.io) or [Brownie](https://eth-brownie.readthedocs.io/en/latest/).

ocean.py is part of the [Ocean Protocol](https://www.oceanprotocol.com) toolset.

This is in beta state. If you run into problems, please open up a [new issue](/issues).

- [🏄 Quickstart](#-quickstart)
- [🦑 Development](#-development)
- [🏛 License](#-license)

## 🏄 Quickstart

Follow these steps in sequence to ramp into Ocean.

 1. **[Install Ocean](READMEs/install.md)**
 2. **[Set up locally](READMEs/setup-local.md)** 
 3. **[Walk through main flow (local setup)](READMEs/main-flow.md)**: publish asset, post for free / for sale, dispense it / buy it, and consume it
 
Now let's do remote flows:

 4. **[Set up remotely](READMEs/setup-remote.md)**
 5. **[Walk through main flow (remote setup)](READMEs/main-flow.md)**. Like step 3, but on wholly remote network
 6. **[Walk through C2D flow](READMEs/c2d-flow.md)** - tokenize & monetize AI algorithm via Compute-to-Data

### Use-case flows

- [Predict-eth](https://github.com/oceanprotocol/predict-eth) - data challenges with prize $$ to predict future ETH price
- [Data Farming](READMEs/df.md) - curate data assets, earn rewards
- [Search & filter data](READMEs/search-and-filter-assets.md) - find assets by tag
- [Key-value database](READMEs/key-value-flow.md) - use data NFTs to store arbitrary key-value pairs on-chain, following ERC725
- [Profile NFTs](READMEs/profile-nfts-flow.md) - enable "login with Web3" where Dapp can access private user profile data


### More types of data assets

Each of the following shows how to publish & consume a particular type of data.
- **[REST API](READMEs/publish-flow-restapi.md)** - Example on Binance ETH price feed
- **[GraphQL](READMEs/publish-flow-graphql.md)** - Example on Ocean Data NFTs
- **[On-chain data](READMEs/publish-flow-onchain.md)** - Example on Ocean swap fees.

### Learn more
- [Understand config parameters](READMEs/parameters.md) - envvars vs files
- [Learn about off-chain services](READMEs/services.md) - Ocean Provider for data services, Aquarius metadata store

## 🦑 Development

- **[Developers flow](READMEs/developers.md)** - to further develop ocean.py
- [Release process](READMEs/release-process.md) - to do a new release of ocean.py

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

