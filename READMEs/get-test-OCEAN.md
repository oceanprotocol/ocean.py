<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Get Test OCEAN and Verify It

As you develop on Ocean, you'll often need to use the OCEAN token. It's an ERC20 token on Ethereum mainnet, along with bridges to other networks and testnet deployments.

Here, let's get some OCEAN for the Goerli testnet, and verify in Python that we have it.

### Setup

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Install the library

## Create a new address / key

In your console, run Python.
```console
python
```

In the Python console:

```python
from eth_account.account import Account
account = Account.create()
print(f"New address: {account.address}")
print(f"New private key: {account.key.hex()}")
```

The address is _randomly_ generated, so our transactions don't overlap with others' on Goerli, which is public.

## Get OCEAN

In your browser:

- Go to the [Goerli OCEAN faucet](https://faucet.goerli.oceanprotocol.com/).
- In that page, supply the address printed above
- It will tell you that test OCEAN are on the way, and report the transaction id (txid). Copy this txid.

## Verify in Etherscan

Let's confirm that we hold the OCEAN, from Etherscan.

In your browser:
- Go to https://goerli.etherscan.io/
- Into the search field, enter txid from the previous step or your Ethereum address. Hit Enter.
- In the results, click on the "ERC20 Token Txns" tab
- You will see the tx that sent you OCEAN.

Alternatively, go straight to this address: ```https://goerli.etherscan.io//token/<OCEAN address>?a=<your account address>```
- Where OCEAN address on Goerli network is listed at https://docs.oceanprotocol.com/core-concepts/networks/#goerli

## Verify in Python

Both Python and Etherscan give views of the same data: your OCEAN balance on the Goerli blockchain.

Now, let's confirm that we hold the OCEAN, from Python.

In a bash console:

`export TEST_PRIVATE_KEY1=<your private key>`

In a Python console:

```python
from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.ocean import Ocean
config = ExampleConfig.get_config("development")  # or any network id configured in your brownie network-config.yaml file
ocean = Ocean(config)

# create an ERC20 object of OCEAN token
print(f"Address of OCEAN token: {ocean.OCEAN_address}")
OCEAN_token = ocean.OCEAN_token

# set wallet
import os
private_key = os.getenv('TEST_PRIVATE_KEY1')
from brownie.network import accounts
wallet = accounts.add(private_key)
print(f"Address of your account: {wallet.address}")

# get balance
OCEAN_balance_in_wei = OCEAN_token.balanceOf(wallet.address)
from web3.main import Web3
OCEAN_balance_in_ether = Web3.fromWei(OCEAN_balance_in_wei, "ether")
print(f"Balance: {OCEAN_balance_in_ether} OCEAN")
if OCEAN_balance_in_wei == 0:
  print("WARNING: you don't have any OCEAN yet")
```

## Further reading

-   [Ocean homepage - OCEAN token info](https://oceanprotocol.com/token)
-   [Developer docs - networks overview](https://docs.oceanprotocol.com/concepts/networks-overview/)
