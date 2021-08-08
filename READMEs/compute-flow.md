<!--
Copyright 2021 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

Note: this README is out of date and will not work. [Here's the issue to fix it](https://github.com/oceanprotocol/ocean.py/issues/101).

# Quickstart: Marketplace Flow with compute-to-data

This tutorial demonstrates publishing a dataset with `compute` service

We will be connecting to the `rinkeby` test net and the Ocean Protocol
supporting services.

Here's the steps:

1.  Setup
2.  Alice publishes assets for data services (= publishes a datatoken contract and metadata)
3.  Alice mints 100 tokens
4.  Alice makes datatokens available for sale in a Balancer pool
5.  Marketplace displays the asset with the available services and price of datatoken
6.  Value swap: Bob buys datatokens from marketplace
7.  Bob uses a service by spending datatoken he just purchased (download)

Let's go through each step.

## 0. Prerequisites and Installation

Use an ethereum account with some eth balance on rinkeby. You can get rinkeby eth using
this [faucet](https://www.rinkeby.io/#faucet). Otherwise, run `ganache-cli` and replace
`rinkeby` with `ganache` when following the steps below.

If you haven't installed yet:

```console
#Install the ocean.py library. Install wheel first to avoid errors.
pip install wheel
pip install ocean-lib
```

## 1. Initialize services

This quickstart treats the publisher/provider service, metadata cache, and marketplace as
externally-run services. For convenience, we run them locally. Refer to each repo for
its own requirements and make sure they all point to `rinkeby` testnet.

[Provider service](https://github.com/oceanprotocol/provider-py)

```console
    docker run oceanprotocol/provider-py:latest
```

[Aquarius (Metadata cache)](https://github.com/oceanprotocol/aquarius)

```console
    docker run oceanprotocol/aquarius:latest
```

[Market app](https://github.com/oceanprotocol/market)

```console
    git clone https://github.com/oceanprotocol/market.git
    cd market
    npm install
    npm start
```

Access the market app in the browser at `http://localhost:8000`.

## 2. Alice publishes assets for data services (= publishes a DataToken contract)

```python
from ocean_lib.common.agreements.service_factory import ServiceDescriptor

from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.data_provider.data_service_provider import DataServiceProvider

#Alice's config
config = {
   'network' : 'rinkeby',
   'metadataCacheUri' : 'http://127.0.0.1:5000',
   'providerUri' : 'http://127.0.0.1:8030'
}
ocean = Ocean(config)
alice_wallet = Wallet(ocean.web3, private_key='8da4ef21b864d2cc526dbdb2a120bd2874c36c9d0a1fb7f8c63d7f7a8b41de8f')
assert alice_wallet.web3.eth.get_balance(alice_wallet.address) > 0, "need ETH"
data_token = ocean.create_data_token('DataToken1', 'DT1', alice_wallet, blob=ocean.config.metadata_cache_uri)
token_address = data_token.address
print(f"token_address: '{token_address}'")

# `ocean.assets.create` will encrypt the URLs using the provider's encrypt service endpoint and update
# the asset before pushing to metadata store
# `ocean.assets.create` will require that token_address is a valid DataToken contract address, unless token_address
# is not provided then the `create` method will first create a new data token and use it in the new
# asset.
metadata =  {
    "main": {
        "type": "dataset", "name": "10 Monkey Species Small", "author": "Mario",
        "license": "CC0: Public Domain", "dateCreated": "2012-02-01T10:55:11Z",
        "files": [
            { "index": 0, "contentType": "application/zip", "url": "https://s3.amazonaws.com/datacommons-seeding-us-east/10_Monkey_Species_Small/assets/training.zip"},
            { "index": 1, "contentType": "text/text", "url": "https://s3.amazonaws.com/datacommons-seeding-us-east/10_Monkey_Species_Small/assets/monkey_labels.txt"},
            { "index": 2, "contentType": "application/zip", "url": "https://s3.amazonaws.com/datacommons-seeding-us-east/10_Monkey_Species_Small/assets/validation.zip"}]}
}

# Prepare attributes for the download service including the cost in DataTokens
service_attributes = {
        "main": {
            "name": "dataAssetAccessServiceAgreement",
            "creator": alice_wallet.address,
            "cost": 1.0, # service cost is 1.0 tokens
            "timeout": 3600 * 24,
            "datePublished": metadata["main"]['dateCreated']
        }
    }

service_endpoint = DataServiceProvider.get_url(ocean.config)
download_service = ServiceDescriptor.access_service_descriptor(service_attributes, service_endpoint)
assert alice_wallet.web3.eth.get_balance(alice_wallet.address) > 0, "need ETH"
asset = ocean.assets.create(metadata, alice_wallet, service_descriptors=[download_service], data_token_address=token_address)
assert token_address == asset.data_token_address

did = asset.did  # did contains the datatoken address
print(f"did: '{did}'")
```
For legacy support, you can also use `metadataStoreUri` instead of `metadataCacheUri`.

## 3. Alice mints 100 tokens

```python
from decimal import Decimal
from ocean_lib.web3_internal.currency import to_wei

data_token.mint(alice_wallet.address, to_wei(Decimal("100.0")), alice_wallet)
```

## 4. Alice creates a pool for trading her new data tokens

```python
from ocean_lib.models.btoken import BToken #BToken is ERC20
OCEAN_token = BToken(ocean.web3, ocean.OCEAN_address)
assert OCEAN_token.balanceOf(alice_wallet.address) > 0, "need OCEAN"

pool = ocean.pool.create(
   token_address,
   data_token_amount=100.0,
   OCEAN_amount=10.0,
   from_wallet=alice_wallet
)
pool_address = pool.address
print(f'DataToken @{data_token.address} has a `pool` available @{pool_address}')
```

## 5. Marketplace posts asset for sale using price obtained from balancer pool

```python
from ocean_lib.common.agreements.service_types import ServiceTypes

from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.currency import from_wei, to_wei
from ocean_lib.models.bpool import BPool

# Market's config
config = {
   'network': 'rinkeby',
}
market_ocean = Ocean(config)

did = ''  # from step 3
pool_address = ''  # from step 4
asset = market_ocean.assets.resolve(did)
service1 = asset.get_service(ServiceTypes.ASSET_ACCESS)
pool = market_ocean.pool.get(market_ocean.web3, pool_address)
# price in OCEAN tokens per data token
OCEAN_address = market_ocean.pool.ocean_address
price_in_OCEAN = market_ocean.pool.calcInGivenOut(
    pool_address, OCEAN_address, token_address, token_out_amount=1.0
)

# Display key asset information, such as the cost of each service
# Each access to an assets service requires ONE datatoken
tokens_amount = 1.0
print(f"Service 1 costs {tokens_amount * price_in_OCEAN} OCEAN")
OCEAN_usd_pool_address = ''
USDT_token_address = ''
ocn_pool = BPool(market_ocean.web3, OCEAN_usd_pool_address)
OCEAN_price = from_wei(ocn_pool.calcInGivenOut(
    ocn_pool.getBalance(USDT_token_address),
    ocn_pool.getDenormalizedWeight(USDT_token_address),
    ocn_pool.getBalance(OCEAN_address),
    ocn_pool.getDenormalizedWeight(OCEAN_address),
    tokenAmountOut_base=to_wei(price_in_OCEAN),
    swapFee_base=ocn_pool.getSwapFee()
))
print(f"Service 1 costs {tokens_amount * price_in_OCEAN * OCEAN_price} USD")
```

## 6. Value swap: Bob buys datatokens from marketplace (using datatoken <> OCEAN balancer pool)

```python
from ocean_lib.web3_internal.wallet import Wallet

bob_wallet = Wallet(ocean.web3, private_key="PASTE BOB'S TEST PRIVATE KEY HERE")
data_token = market_ocean.get_data_token(token_address)
# This assumes bob_wallet already has sufficient OCEAN tokens to buy the data token. OCEAN tokens
# can be obtained through a crypto exchange or an on-chain pool such as balancer or uniswap
market_ocean.pool.buy_data_tokens(
    pool_address,
    amount=1.0, # buy one data token
    max_OCEAN_amount=price_in_OCEAN, # pay maximum 0.1 OCEAN tokens
    from_wallet=bob_wallet
)

print(f'bob has {data_token.token_balance(bob_wallet.address} datatokens.')
```

## 7. Bob uses a service from the asset he just purchased (download)

```python

market_address = '0x<markets ethereum address to receive service fee'
service = asset.get_service(ServiceTypes.ASSET_ACCESS)  # asset from step 5
quote = market_ocean.assets.order(asset.did, bob_wallet.address, service_index=service.index)
order_tx_id = market_ocean.assets.pay_for_service(
    market_ocean.web3,
    quote.amount, quote.data_token_address, asset.did, service.index, market_address, bob_wallet
)
file_path = market_ocean.assets.download(
    asset.did,
    service.index,
    bob_wallet,
    order_tx_id,
    destination='~/my-datasets'
)
```
