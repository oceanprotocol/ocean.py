
# ocean-lib

`ocean-lib` is a Python library to privately & securely publish, exchange, 
and consume data. With it, you can:
- **Publish** data services: downloadable files or compute-to-data. 
Ocean creates a new [ERC20](https://github.com/ethereum/EIPs/blob/7f4f0377730f5fc266824084188cc17cf246932e/EIPS/eip-20.md) 
datatoken for each dataset / data service.
- **Mint** datatokens for the service
- **Sell** datatokens via an OCEAN-datatoken Balancer pool (for auto price discovery), or for a fixed price
- **Stake** OCEAN on datatoken pools
- **Consume** datatokens, to access the service
- **Transfer** datatokens to another owner, and **all other ERC20 actions** 
using [web3.py](https://web3py.readthedocs.io/en/stable/examples.html#working-with-an-erc20-token-contract) etc.


`ocean-lib` is part of the [Ocean Protocol](https://www.oceanprotocol.com) toolset.

## Quick Install

```pip install ocean-lib```

## Getting Started

1. **[Publish your first datatoken](READMEs/datatokens_flow.md)**. Connect to Ethereum, create an Ocean instance, and publish your first datatoken.

2. **[Get an overview of ocean-lib](READMEs/overview.md)** key modules and functions.

3. **[Learn more about Ocean service providers](READMEs/providers.md)**

4. **[Learn more about wallets](READMEs/wallets.md)** - other ways to connect wallets.

5. **[Create a marketplace and sell data](READMEs/marketplace_flow.md)**. Batteries-included flow including metadata and consuming datatokens.

## For ocean-lib Developers

If you want to further develop ocean-lib, then [please go here](READMEs/developers.md).

## License

```
Copyright ((C)) 2021 Ocean Protocol Foundation

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
