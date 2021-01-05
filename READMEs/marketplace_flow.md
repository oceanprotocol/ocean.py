# Quickstart: Marketplace Flow

This quickstart describes how to publish data assets as datatokens (including metadata), post the datatokens to a marketplace, buy datatokens, and consume datatokens (including download). It focuses on Alice's experience as a publisher, and Bob's experience as a buyer & consumer. The rest are services used by Alice and Bob.

Here are the steps:
1. Setup
1. Alice publishes data asset (including metadata)
1. Alice mints 100 tokens
1. Alice creates a pool for trading her new datatokens
1. Marketplace displays the asset with the available services and price of datatoken
1. Value swap: Bob buys datatokens from marketplace
1. Bob uses a service by spending datatoken he just purchased (download)
1. Bonus: run your own local Provider or Metadata cache (Aquarius)
1. Bonus: Get datatoken price in USD

Let's go through each step.

## 1. Setup

Please do the datatokens tutorial before this one, so that you've...
* installed ocean-lib
* got an Ethereum account on rinkeby that holds ETH. You've exported its private key.
* got an infura account, with your infura project id
* set up a `config.ini` file. It has:
```
[eth-network]
network = https://rinkeby.infura.io/v3/<your infura project id>
```

Then, in `config.ini` file, add:
```
[resources]
aquarius.url = https://provider.rinkeby.v3.dev-ocean.com
provider.url = https://aquarius.rinkeby.v3.dev-ocean.com
```

Then, in console:
```
export MY_TEST_KEY=<my_private_key>
```

Finally, set up the service for the [Market app](https://github.com/oceanprotocol/market). In a new console:
```
git clone https://github.com/oceanprotocol/market.git
cd market
npm install
npm start
```

The market app can be seen as a webapp at `http://localhost:8000`.  

## 2. Alice publishes data asset (including metadata)

What follows is in Python. First, configure the components and create an `Ocean` instance.
```python
import os

from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_utils.agreements.service_factory import ServiceDescriptor

#Alice's config
config = {
   'network' : os.getenv('NETWORK_URL'),
   'metadataStoreUri' : os.getenv('AQUARIUS_URL'),
   'providerUri' : os.getenv('PROVIDER_URL'),
}
ocean = Ocean(config)
```

Next, create a `Wallet` for Alice.
```python
alice_wallet = Wallet(ocean.web3, private_key=os.getenv('MY_TEST_KEY'))
```

Publish a datatoken.
```
data_token = ocean.create_data_token('DataToken1', 'DT1', alice_wallet, blob=ocean.config.metadata_store_url)
token_address = data_token.address
```

Specify the service attributes, and connect that to `service_endpoint` and `download_service`.
```python
date_created = "2012-02-01T10:55:11Z"
service_attributes = {
        "main": {
            "name": "dataAssetAccessServiceAgreement",
            "creator": alice_wallet.address,
            "timeout": 3600 * 24,
            "datePublished": date_created,
            "cost": 1.0, # <don't change, this is obsolete>
        }
    }

service_endpoint = DataServiceProvider.get_url(ocean.config)
download_service = ServiceDescriptor.access_service_descriptor(service_attributes, service_endpoint)
```

Metadata is information about the data asset. Ocean stores it on-chain, enabling permissionless access by anyone.

We also want a convenient place for the Provider to store the service urls without requiring a separate storage facility, while making the urls available only to datatoken owners. To solve this, the Provider *encrypts* the urls and lumps them in with the rest of the metadata (the plaintext part), to be stored on-chain. The Provider will decrypt as part of the data provisioning.

```python
metadata =  {
    "main": {
        "type": "dataset", "name": "10 Monkey Species Small", "author": "Mario", 
        "license": "CC0: Public Domain", "dateCreated": date_created, 
        "files": [
            { "index": 0, "contentType": "application/zip", "url": "https://s3.amazonaws.com/datacommons-seeding-us-east/10_Monkey_Species_Small/assets/training.zip"},
            { "index": 1, "contentType": "text/text", "url": "https://s3.amazonaws.com/datacommons-seeding-us-east/10_Monkey_Species_Small/assets/monkey_labels.txt"},
            { "index": 2, "contentType": "application/zip", "url": "https://s3.amazonaws.com/datacommons-seeding-us-east/10_Monkey_Species_Small/assets/validation.zip"}]}
}

#ocean.assets.create will encrypt URLs using Provider's encrypt service endpoint, and update asset before putting on-chain.
#It requires that token_address is a valid DataToken contract address. If that isn't provided, it will create a new token.
asset = ocean.assets.create(metadata, alice_wallet, service_descriptors=[download_service], data_token_address=token_address)
assert token_address == asset.data_token_address

did = asset.did  # did contains the datatoken address
```

## 3. Alice mints 100 datatokens

```python

data_token.mint_tokens(alice_wallet.address, 100.0, alice_wallet)
```

## 4. Alice creates a pool for trading her new datatokens

First, [first get Rinkeby OCEAN via this faucet](https://faucet.rinkeby.oceanprotocol.com/).

Then, in Python:
```python
pool = ocean.pool.create(
   token_address,
   data_token_amount=100.0,
   OCEAN_amount=10.0,
   from_wallet=alice_wallet
)
pool_address = pool.address
print(f'DataToken @{data_token.address} has a `pool` available @{pool_address}')
```

## 5. Marketplace displays asset for sale 

Up til now, all the actions have been by Alice. Let's switch now to the perspective to that of the Marketplace operator. They can display for sale whatever data assets they see on chain which are in a pool (or a fixed-price exchange). 

Here, we show how the marketplace might grab info about the data asset, price info from the pool, and show it in text form. It can also be in the webapp of course.

First, the market creates its own `Ocean` instance.
```python
import os
from ocean_utils.agreements.service_types import ServiceTypes

from ocean_lib.ocean.ocean import Ocean
from ocean_lib.ocean.util import from_base_18
from ocean_lib.models.bpool import BPool

# Market's config
config = {
   'network': os.getenv('NETWORK_URL'),
}
market_ocean = Ocean(config)
```

Next, the market creates an object pointing to the pool.
```python
did = ''  # from step 3
pool_address = ''  # from step 4
asset = market_ocean.assets.resolve(did)
service1 = asset.get_service(ServiceTypes.ASSET_ACCESS)
pool = market_ocean.pool.get(pool_address)
```

To access a data service, you need 1.0 datatokens. Here, the market retrieves the datatoken price denominated in OCEAN.
```python
OCEAN_address = market_ocean.pool.ocean_address
price_in_OCEAN = market_ocean.pool.calcInGivenOut(
    pool_address, OCEAN_address, token_address, token_out_amount=1.0
)
print(f"Price of 1 datatoken is {price_in_OCEAN} OCEAN")
```

## 6. Value swap: Bob buys datatokens from marketplace (using datatoken <> OCEAN balancer pool)

Now, we're going to be Bob. Bob wants to buy datatokens from Alice, through the marketplace. For that, Bob needs some Rinkeby ETH and his own private key. You can follow the same steps like in step 0. It culminates in (from terminal): `export BOB_KEY=<Bob_private_key>`

Next, Bob will need OCEAN to buy the datatoken. [Here's](https://faucet.rinkeby.oceanprotocol.com/) a Rinkeby faucet for OCEAN. More information is [here](https://docs.oceanprotocol.com/tutorials/get-ether-and-ocean-tokens/).

Then, here's the Python from Bob's perspective.
```python
# <FIRST: copy and paste the code from step 5 here>

import os
from ocean_lib.ocean.util import to_base_18
from ocean_lib.web3_internal.wallet import Wallet

bob_wallet = Wallet(ocean.web3, private_key=os.getenv('BOB_KEY'))
data_token = market_ocean.get_data_token(token_address)

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

## 8. Bonus round: run Provider and Aquarius locally

Bonus round time! So far, we've used third-party services for Provider and Aquarius (Metadata cache). Now, let's run them locally.

### Aquarius (Metadata cache)
- Go to [Aquarius' repo](https://github.com/oceanprotocol/aquarius), check its requirements, and make sure it points to Rinkeby.
- In a new terminal: `docker run oceanprotocol/aquarius:latest` (or other ways, as repo describes)
- Point the appropriate envvar to it. In your terminal: `export AQUARIUS_URL=<the url that it says "Listening at">`

### Provider
- Go to [Ocean Provider's repo](https://github.com/oceanprotocol/provider), check its requirements, and make sure it points to Rinkeby.
- In another new terminal: `docker run oceanprotocol/provider:latest` (or other ways, as repo describes)
- Point the appropriate envvar to it. In your terminal: `export PROVIDER_URL=<the url that it says "Listening at">`

## 9. Bonus round: get price of datatoken in USD

This extends step 5. Whereas step 5 showed the price of a datatoken in OCEAN, we could also get it in USD. How? Find the USDT : OCEAN exchange from another pool.

```python
OCEAN_usd_pool_address = '' #get externally
USDT_token_address = '' #get externally
ocn_pool = BPool(OCEAN_usd_pool_address)
OCEAN_price = from_base_18(ocn_pool.calcInGivenOut(
    ocn_pool.getBalance(USDT_token_address), 
    ocn_pool.getDenormalizedWeight(USDT_token_address),
    ocn_pool.getBalance(OCEAN_address), 
    ocn_pool.getDenormalizedWeight(OCEAN_address),
    tokenAmountOut_base=to_base_18(price_in_OCEAN),
    swapFee_base=ocn_pool.getSwapFee()
))
print(f"1 datatoken costs {price_in_OCEAN * OCEAN_price} USD")
