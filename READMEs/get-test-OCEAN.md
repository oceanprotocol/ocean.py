<!--
Copyright 2021 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Get Test OCEAN and Verify It

As you develop on Ocean, you'll often need to use the OCEAN token. It's an ERC20 token on Ethereum mainnet, along with testnet deployments.

Here, let's get some OCEAN for the Rinkeby testnet, and verify in Python that we have it.

## Setup

This builds on the setup in the following. Please do it first.

-   [Datatokens tutorial](datatokens-flow.md)

## Get OCEAN

[Get Rinkeby OCEAN via this faucet](https://faucet.rinkeby.oceanprotocol.com/).

It will tell you that test OCEAN are on the way, and report the transaction id (txid). Copy this txid.

Go to https://rinkeby.etherscan.io, and search for the txid. You will see the tx that sent you OCEAN.

## Verify in Python

Let's see that we hold the OCEAN, in Python:

```python
#setup
import os
from ocean_lib.ocean.ocean import Ocean
config = {'network': os.getenv('NETWORK_URL')}
ocean = Ocean(config)

#create an ERC20 object
print(f"Address of OCEAN token: {ocean.OCEAN_address}")
from ocean_lib.models.btoken import BToken #BToken is ERC20
OCEAN_token = BToken(ocean.web3, ocean.OCEAN_address)

#set wallet
private_key = os.getenv('MY_TEST_KEY')
from ocean_lib.web3_internal.wallet import Wallet
wallet = Wallet(ocean.web3, private_key=private_key)
print(f"Address of your account: {wallet.address}")

#get balance
OCEAN_balance_base18 = OCEAN_token.balanceOf(wallet.address) #like wei
from ocean_lib.ocean import util
OCEAN_balance = util.from_base_18(OCEAN_balance_base18) #like eth
print(f"Balance: {OCEAN_balance} OCEAN")
if OCEAN_balance == 0.0:
  print("WARNING: you don't have any OCEAN yet")
```

## Verify in Etherscan

Let's see that we hold the OCEAN, in Etherscan.

Open this url in your browser to see your account's OCEAN balance. (If you need, the Python code above printed both addresses).

```console
    https://rinkeby.etherscan.io/token/<OCEAN address>?a=<your account address>
```

Both Python and Etherscan give views of the same data: your OCEAN balance on the Rinkeby blockchain.

## Further reading

-   [Ocean homepage - OCEAN token info](https://oceanprotocol.com/token)
-   [Developer docs - networks overview](https://docs.oceanprotocol.com/concepts/networks-overview/)
