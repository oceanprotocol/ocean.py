<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Structures

ocean.py offers a variety of methods to deal with Ocean smart contracts.
For most smart contract functions that accept tuples or lists, you are free to design the structure yourself.

However, ocean.py offers helpers to deal with the trouble of ABI-matching, by providing a few NamedTuple instances
that mirror the ABI structure. Typings and examples inside ocean.py will guide you in using the predefined structures.

You will find these models inside `ocean_lib/models/models_structures`. You are free to use (and contribute to)
these, or choose the option of hand-coded structures.

In most cases, by using the Ocean class and utils directly, this functionality is offered out of the box,
and you won't have to deal with this choice at all.

##  Example

Let's take the example of CreateERC721Data. In order to create an ERC721 token, the contract ABI requires
users to send the name, symbol, template index, additional ERC20 deployer and token uri.

Assuming some basic data, you can send this to the function as a tuple:
`("NFT", "NFTSYMBOL", 1, ZERO_ADDRESS, "https://oceanprotocol.com/nft/")`

Or a dictionary:
```python
{
    "name": "NFT",
    "symbol": "NFTSYMBOL",
    "_templateIndex": 1,
    "additionalERC20Deployer": ZERO_ADDRESS,
    "tokenURI": "https://oceanprotocol.com/nft/"
}
```

Please note that, for dictionaries, you need to match the ABI parameter names precisely, including casing.
Since dictionaries are not ordered, the order will be derived by web3.py based on the ordering in the ABI.

Our approach to modeling structure combines the order-based tuple logic with the readability of dictionaries.

```python
from ocean_lib.models.models_structures import CreateERC721Data

erc721_data = CreateERC721Data(
    name="NFT",
    symbol="NFTSYMBOL",
    template_index=1,
    additional_erc20_deployer=ZERO_ADDRESS,
    token_uri="https://oceanprotocol.com/nft/",
)
```

It is easy to identify which element of the tuple represents which concept,
but the fixed args mean that you need not concern with the ABI names and we leverage the order-based logic.

## Note on web3.py support
There is currently a bug in ethereum/web3.py where NamedTuples are not correctly typed.
To mitigate that, we are currently implementing a conversion in ocean.py, at the model level.
However, this issue will soon be more elegantly fixed. There is already a PR in review on ethereum/web3.py
initiated by the ocean.py team.
