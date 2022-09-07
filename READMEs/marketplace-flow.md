<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Marketplace Flow

This quickstart describes where Bob buys datatokens for OCEAN using the fixed-rate exchange flow. 

It focuses on Alice's experience as a publisher, and Bob's experience as a buyer & consumer.

Here are the steps:

1.  Setup
2.  Alice publishes Data NFT & Datatoken
3.  Alice creates an OCEAN-datatoken exchange 
4.  Bob buys datatokens with OCEAN

Let's go through each step.

## 1. Setup

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library from v4 sources
- [x] Setup : Set envvars
- [x] Setup : Setup in Python

### Create fake OCEAN

For testing purposes, we can create fake OCEAN by leveraging Ocean token factory. In the same Python console:
```python
# Set factory envvar. Staying in Python console lets you retain state from previous READMEs.
import os
os.environ['FACTORY_DEPLOYER_PRIVATE_KEY'] = '0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58'

# Mint fake OCEAN. Alice & Bob automatically get some.
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
mint_fake_OCEAN(config)

OCEAN_token = ocean.OCEAN_token
```

## 2. Alice publishes Data NFT & Datatoken

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do:
- [x] 2.1 Create a data NFT
- [x] 2.2 Create a datatoken from the data NFT

Then, have Alice mint datatokens. In the same Python console:
```python
datatoken.mint(alice_wallet.address, ocean.to_wei(100), alice_wallet)
```

## 3. Alice creates an OCEAN-datatoken exchange

In the same Python console:
```python
exchange_id = ocean.create_fixed_rate(
    datatoken=datatoken,
    base_token=OCEAN_token,
    amount=ocean.to_wei(100),
    fixed_rate=ocean.to_wei(1),
    from_wallet=alice_wallet,
)
```

Instead of using OCEAN, Alice could have used H2O, the OCEAN-backed stable asset. Or, she could have used USDC, WETH, or other, for a slightly higher fee.

## 4. Bob buys datatokens with OCEAN

Now, you're Bob. In the same Python console:
```python
# Bob sets up wallet
bob_private_key = os.getenv('TEST_PRIVATE_KEY2')
bob_wallet = Wallet(ocean.web3, bob_private_key, config.block_confirmations, config.transaction_timeout)
print(f"bob_wallet.address = '{bob_wallet.address}'")

# Bob verifies having enough funds
assert ocean.web3.eth.get_balance(bob_wallet.address) > 0, "need ganache ETH"
assert OCEAN_token.balanceOf(bob_wallet.address) > 0, "need OCEAN"

# Bob retrieves the address of the exchange to use.
#   For convenience, we the object that Alice created.
#   In practice, Bob might use search or other means. See the "Tips & Tricks" section for details.
exchange_address = ocean.fixed_rate_exchange.address

# Bob allows the exchange contract to spend some OCEAN
OCEAN_token.approve(exchange_address, ocean.to_wei(100), bob_wallet)

# Bob starts the exchange. The contract takes some of his OCEAN and adds datatokens.
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
tx_result = ocean.fixed_rate_exchange.buy_dt(
    exchange_id=exchange_id,
    datatoken_amount=ocean.to_wei(20),
    max_base_token_amount=ocean.to_wei(50),
    consume_market_swap_fee_address=ZERO_ADDRESS,
    consume_market_swap_fee_amount=0,
    from_wallet=bob_wallet,
)
assert tx_result, "failed buying datatokens at fixed rate for Bob"
```

## Appendix. Tips & Tricks

You can combine the transactions to (a) publish data NFT, (b) publish datatoken, and (c) publish exchange into a _single_ transaction, via the method `create_nft_erc20_with_fixed_rate()`.

If you already created the `exchange_id`, then you can reuse it.

If an exchange has been created before or there are other exchanges for a certain datatoken, it can be searched by providing the datatoken address. In Python consodle:
```python
# Get a list exchange addresses and ids with a given datatoken and exchange owner.
datatoken_address = datatoken.address
nft_factory = ocean.get_nft_factory()
exchange_addresses_and_ids = nft_factory.search_exchange_by_datatoken(ocean.fixed_rate_exchange, datatoken_address)

# And, we can filter results by the exchange owner.
exchange_addresses_and_ids = nft_factory.search_exchange_by_datatoken(ocean.fixed_rate_exchange, datatoken_address, alice_wallet.address)
print(exchange_addresses_and_ids)
```

