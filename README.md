
# ocean-lib

`ocean-lib` is a Python library to privately & securely publish, exchange, 
and consume data. With it, you can:
* **Publish** data services: downloadable files or compute-to-data. 
Ocean creates a new [ERC20](https://github.com/ethereum/EIPs/blob/7f4f0377730f5fc266824084188cc17cf246932e/EIPS/eip-20.md) 
datatoken for each data set.
* **Mint** datatokens to allow buying/consuming the data service
* **Consume** datatokens, to access the service
* **Transfer** datatokens to another owner, and **all other ERC20 actions** 
using [web3.py](https://web3py.readthedocs.io/en/stable/examples.html#working-with-an-erc20-token-contract) etc.
* **Price** datatokens in terms of OCEAN tokens by creating a Balancer pool of `datatoken <> OCEAN`
* **Stake** OCEAN tokens on specific datatokens (by adding OCEAN liquidity into a datatoken Balancer pool)
* Buy datatokens from available Balancer pools or from fixed price exchange if available
* And much more ...


`ocean-lib` is part of the [Ocean Protocol](https://www.oceanprotocol.com) toolset.

## Quick Install

```pip install ocean-lib```

## Quickstart

### Setup config file and env't variables

This guide demonstrates how to [setup the config file and environment variables](READMEs/setup.md)

### ocean-lib overview

[Description of ocean-lib modules and functions](READMEs/overview.md)

### Marketplace Flow

This batteries-included flow includes metadata, download service and datatoken.

[Go to marketplace flow](READMEs/marketplace_flow.md)

## For ocean-lib Developers

[Go to developers flow](READMEs/developers.md)

## License

```
Copyright ((C)) 2020 Ocean Protocol Foundation

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
