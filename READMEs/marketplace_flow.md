# Quickstart: Marketplace Flow

This quickstart describes a batteries-included flow including using off-chain services for metadata (Aquarius) and consuming datasets (Provider).

It focuses on Alice's experience as a publisher, and Bob's experience as a buyer & consumer. 

Here are the steps:
1. Setup
1. Alice publishes data asset (including metadata)
1. Alice mints 100 tokens
1. Alice creates a pool for trading her new datatokens
1. Market displays the asset for sale
1. Value swap: Bob buys datatokens from market
1. Bob uses a service by spending datatoken he just purchased (download)

Bonus rounds:
1. Bonus: run your own local Provider or Aquarius
1. Bonus: Get datatoken price in USD

Let's go through each step.

## 1. Setup

This builds on the setups in the following. Please do them first.
 * [Datatokens tutorial](datatokens_flow.md)
 * [Get test OCEAN](get_test_OCEAN.md)

Then, set urls for metadata and provider services as envvars. In the console:
```
export AQUARIUS_URL=https://aquarius.rinkeby.oceanprotocol.com
export PROVIDER_URL=https://provider.rinkeby.oceanprotocol.com
```

Then, set up the service for the [Market app](https://github.com/oceanprotocol/market). In a *new* console:
```
git clone https://github.com/oceanprotocol/market.git
cd market
npm install
npm start
```

Finally, check out the market app as a webapp, at `http://localhost:8000`. 

## 2. Alice publishes data asset (including metadata)

What follows is in Python, from your main console. 
```python
#setup Alice's ocean instance
import os
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_utils.agreements.service_factory import ServiceDescriptor
config = {
   'network' : os.getenv('NETWORK_URL'),
   'metadataStoreUri' : os.getenv('AQUARIUS_URL'),
   'providerUri' : os.getenv('PROVIDER_URL'),
}
ocean = Ocean(config)

#Alice's wallet
from ocean_lib.web3_internal.wallet import Wallet
alice_wallet = Wallet(ocean.web3, private_key=os.getenv('MY_TEST_KEY'))
```

Publish a datatoken.
```
print("create datatoken: begin")
data_token = ocean.create_data_token('DataToken1', 'DT1', alice_wallet, blob=ocean.config.metadata_store_url)
token_address = data_token.address
print("create datatoken: done")
print(f"token_address = '{token_address}'")
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
print(f"did = '{did}'") 
```

## 3. Alice mints 100 datatokens

```python

data_token.mint_tokens(alice_wallet.address, 100.0, alice_wallet)
```

## 4. Alice creates a pool for trading her new datatokens

Alice needs Rinkeby OCEAN for this step. Let's check. If this fails, the tutorial to [get test OCEAN](get_test_OCEAN.md) will help.
```python
from ocean_lib.models.btoken import BToken #BToken is ERC20
OCEAN_token = BToken(ocean.OCEAN_address)
assert OCEAN_token.balanceOf(alice_wallet.address) > 0, "need Rinkeby OCEAN"
```

Let's do the actual work to create the pool. It will do several blockchain transactions: create the base pool, bind OCEAN and datatoken, add OCEAN and datatoken liquidity, and finalize the pool. 
```python
pool = ocean.pool.create(
   token_address,
   data_token_amount=100.0,
   OCEAN_amount=10.0,
   from_wallet=alice_wallet
)
pool_address = pool.address
print(f"pool_address = '{pool_address}'")
```

## 5. Marketplace displays asset for sale 

Up until now, all the actions have been by Alice. Let's switch now to the perspective to that of the Marketplace operator. They can display for sale whatever data assets they see on chain which are in a pool (or a fixed-price exchange). 

Here, we show how the marketplace might grab info about the data asset, price info from the pool, and show it in text form. It can also be in the webapp of course.

Stop and re-start your Python console. What follows is in Python.

```python
#setup market's ocean instance
import os
from ocean_lib.ocean.ocean import Ocean
config = {
   'network' : os.getenv('NETWORK_URL'),
   'metadataStoreUri' : os.getenv('AQUARIUS_URL'),
   'providerUri' : os.getenv('PROVIDER_URL'),
}
market_ocean = Ocean(config)
```

The market will know the token, etc that it's looking for. For this quickstart, we simply paste in the values that were printed in previous steps.
```python
token_address = '<printed earlier>'
did = '<printed earlier>'
pool_address = '<printed earlier>'
```

Next, create objects pointing to the service and pool
```python
#point to service
from ocean_utils.agreements.service_types import ServiceTypes
asset = market_ocean.assets.resolve(did)
service1 = asset.get_service(ServiceTypes.ASSET_ACCESS)

#point to pool
pool = market_ocean.pool.get(pool_address)
```

To access a data service, you need 1.0 datatokens. Here, the market retrieves the datatoken price denominated in OCEAN.
```python
OCEAN_address = market_ocean.OCEAN_address
price_in_OCEAN = market_ocean.pool.calcInGivenOut(
    pool_address, OCEAN_address, token_address, token_out_amount=1.0)
print(f"Price of 1 datatoken is {price_in_OCEAN} OCEAN")
```

## 6. Value swap: Bob buys datatokens from market

Now, we're going to be Bob. Bob wants to buy datatokens from Alice, through the marketplace using the OCEAN-datatokens pool.

First, Bob will need his own Rinkeby Ethereum account / private key, Rinkeby ETH, and Rinkeby OCEAN.
 * Get account and ETH with help from the [datatokens tutorial](datatokens_flow.md). Then, in console: `export BOB_KEY=<Bob_private_key>`
 * Get OCEAN with help from [test OCEAN tutorial](get_test_OCEAN.md)

Stop and re-start your Python console. What follows is in Python.

Set up Ocean and wallet.
```python
#setup Bob's ocean instance
import os
from ocean_lib.ocean.ocean import Ocean
config = {
   'network' : os.getenv('NETWORK_URL'),
   'metadataStoreUri' : os.getenv('AQUARIUS_URL'),
   'providerUri' : os.getenv('PROVIDER_URL'),
}
bob_ocean = Ocean(config)

#Bob's wallet
from ocean_lib.web3_internal.wallet import Wallet
bob_wallet = Wallet(bob_ocean.web3, private_key=os.getenv('BOB_KEY'))
print(f"bob_wallet.address = '{bob_wallet.address}'")
```

Verify that Bob has Rinkeby ETH. If it fails, the [datatokens tutorial](datatokens_tutorial.md) can help.
```python
assert bob_ocean.web3.eth.getBalance(bob_wallet.address) > 0, "need Rinkeby ETH"
```

Verify that Bob has Rinkeby OCEAN. If it fails, the [test OCEAN tutorial](get_test_OCEAN.md) can help.
```python
from ocean_lib.models.btoken import BToken #BToken is ERC20
OCEAN_token = BToken(bob_ocean.OCEAN_address)
assert OCEAN_token.balanceOf(bob_wallet.address) > 0, "need Rinkeby OCEAN"
```

Fill in values printed earlier. Bob will know these. For this quickstart, paste it in.
```python
token_address = '<printed earlier>'
pool_address = '<printed earlier>'
did = '<printed earlier>'
```

Bob buys 1.0 datatokens - the amount needed to consume the dataset.
```python
data_token = bob_ocean.get_data_token(token_address)

bob_ocean.pool.buy_data_tokens(
    pool_address, 
    amount=1.0, # buy 1.0 datatoken
    max_OCEAN_amount=10.0, # pay up to 10.0 OCEAN
    from_wallet=bob_wallet
)

print(f"Bob has {data_token.token_balance(bob_wallet.address)} datatokens.")

assert data_token.balanceOf(bob_wallet.address) >= 1.0, "Bob didn't get 1.0 datatokens"
```
   
## 7. Bob uses a service from the asset he just purchased (download)

```python
fee_receiver = None # could also be market address

#asset from step 5
from ocean_utils.agreements.service_types import ServiceTypes
asset = bob_ocean.assets.resolve(did)
service = asset.get_service(ServiceTypes.ASSET_ACCESS)

#order the asset, and send over the datatoken
quote = bob_ocean.assets.order(asset.did, bob_wallet.address, service_index=service.index)
order_tx_id = bob_ocean.assets.pay_for_service(
    quote.amount, quote.data_token_address, asset.did, service.index, fee_receiver, bob_wallet)
print(f"order_tx_id = '{order_tx_id}'")
```

Now, download to cwd. If the connection breaks, Bob can request again by showing the `order_tx_id`.
```
file_path = bob_ocean.assets.download(
    asset.did, 
    service.index, 
    bob_wallet, 
    order_tx_id, 
    destination='./' 
)
print(f"file_path = '{file_path}'")
```

# Bonus Rounds

## Bonus round 1: run Provider and Aquarius locally

Bonus round time! So far, we've used third-party services for Provider and Aquarius (Metadata cache). Now, let's run them locally.

### Aquarius (Metadata cache)
- Go to [Aquarius' repo](https://github.com/oceanprotocol/aquarius), check its requirements, and make sure it points to Rinkeby.
- In a new terminal: `docker run oceanprotocol/aquarius:latest` (or other ways, as repo describes)
- Point the appropriate envvar to it. In your terminal: `export AQUARIUS_URL=<the url that it says "Listening at">`

### Provider
- Go to [Ocean Provider's repo](https://github.com/oceanprotocol/provider), check its requirements, and make sure it points to Rinkeby.
- In another new terminal: `docker run oceanprotocol/provider:latest` (or other ways, as repo describes)
- Point the appropriate envvar to it. In your terminal: `export PROVIDER_URL=<the url that it says "Listening at">`

## Bonus round 2: get price of datatoken in USD

This extends step 5. Whereas step 5 showed the price of a datatoken in OCEAN, we could also get it in USD. How? Find the USDT : OCEAN exchange from another pool.

```python
from ocean_lib.models.bpool import BPool
from ocean_lib.ocean.util import from_base_18

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
