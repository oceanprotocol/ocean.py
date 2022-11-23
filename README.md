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

- **[Installation flow](READMEs/install.md)** - the required setup to run ocean.py flows.
- **[Simple flow](READMEs/data-nfts-and-datatokens-flow.md)** - the essence of Ocean - creating a data NFT & datatoken.
- **[Publish flow](READMEs/publish-flow.md)** - a dataset is published.
- **[Consume flow](READMEs/consume-flow.md)** - a published dataset is consumed (downloaded).
- **[Marketplace flow](READMEs/marketplace-flow.md)** - a data asset is posted for sale at fixed rate, then purchased.
- **[Dispenser flow](READMEs/dispenser-flow.md)** - here, a datatoken dispenser is created and datatokens are dispensed for free.
- **[Search & filter data assets](READMEs/search-and-filter-assets.md)** - how assets can be found by their `tags` via Aquarius.

### Remote flows

- **[Get test MATIC](READMEs/get-test-MATIC.md)** - from Mumbai network
- **[Simple remote flow](READMEs/simple-remote.md)** - like the simple flow, but using _remote_ services.
- **[Compute-to-data flow](READMEs/c2d-flow.md)** - uses C2D to build an AI model.

### More types of data assets

- **[REST API flow](READMEs/publish-flow-restapi.md)** - publish & consume REST API-style URIs, showing Binance ETH price feed
- **[GraphQL flow](READMEs/publish-flow-graphql.md)** - publish & consume GraphQL-style URIs
- **[On-chain data flow](READMEs/publish-flow-onchain.md)** - publish & consume on-chain data

### Key-value flows

- [Key-value database](READMEs/key-value-flow.md) - use data NFTs to store arbitrary key-value pairs on-chain.
- [Profile NFTs](READMEs/profile-nfts-flow.md) - enable "login with Web3" where Dapp can access private user profile data.

### Data Challenge flows

- [Predict-eth repo](https://github.com/oceanprotocol/predict-eth) - data challanges with $ to predict future ETH price.

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
