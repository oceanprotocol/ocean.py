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
- **Transfer** data NFTs & datatokens to another owner, and **all other ERC721 & ERC20 actions** using [web3.py](https://web3py.readthedocs.io), [Brownie](https://eth-brownie.readthedocs.io/en/latest/), etc.

ocean.py is part of the [Ocean Protocol](https://www.oceanprotocol.com) toolset.

This is in beta state. If you run into problems, please open up a [new issue](/issues).

- [🏄 Quickstart](#-quickstart): simple flow, marketplace, compute-to-data, more
- [🦑 Development](#-development)
- [🏛 License](#-license)

## 🏄 Quickstart

Here are flows to try out, from simple to specific detailed variants.

- **[Installation](READMEs/install.md)** - need for each flow below
- **[Simple flow](READMEs/data-nfts-and-datatokens-flow.md)** - publish a dataset's data NFT and datatoken
- **[Publish flow](READMEs/publish-flow.md)** - publish a dataset's data NFT, datatoken _and_ metadata (DDO)
- **[Consume flow](READMEs/consume-flow.md)** - download a dataset
- **[Post priced data](READMEs/marketplace-flow.md)** - post a dataset for sale, having a fixed price
- **[Post free data](READMEs/dispenser-flow.md)** - post a dataset for free, via a faucet
- **[Search & filter data](READMEs/search-and-filter-assets.md)** - find assets by tag

### Remote flows

- **[Get test MATIC](READMEs/get-test-MATIC.md)** - from Mumbai network
- **[Simple remote flow](READMEs/simple-remote.md)** - like the simple flow, but using _remote_ services
- **[C2D flow](READMEs/c2d-flow.md)** - uses Compute-to-Data to build an AI model

### More types of data assets

- **[REST API flow](READMEs/publish-flow-restapi.md)** - publish & consume REST API data, showing Binance ETH price feed
- **[GraphQL flow](READMEs/publish-flow-graphql.md)** - publish & consume GraphQL data
- **[On-chain data flow](READMEs/publish-flow-onchain.md)** - publish & consume on-chain data

### Key-value flows

- [Key-value database](READMEs/key-value-flow.md) - use data NFTs to store arbitrary key-value pairs on-chain, following ERC725
- [Profile NFTs](READMEs/profile-nfts-flow.md) - enable "login with Web3" where Dapp can access private user profile data

### Use-case flows

- [Predict-eth](https://github.com/oceanprotocol/predict-eth) - data challenges with $ to predict future ETH price
- [Data Farming](READMEs/df.md) - curate data assets, earn rewards

### Learn more

- [Get test OCEAN](READMEs/get-test-OCEAN.md) - from Goerli
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

