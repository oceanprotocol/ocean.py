# Quickstart: Marketplace Flow

This batteries-included flow includes metadata, multiple services for one datatoken, and compute-to-data.

It focuses on Alice's experience as a publisher, and Bob's experience as a buyer & consumer. The rest are services used by Alice and Bob.

Here's the steps.
1. Initialize services
1. Alice publishes assets for data services (= publishes a datatoken contract and metadata)
1. Alice mints 100 tokens
1. Alice allows marketplace to sell her datatokens
1. Marketplace posts asset for sale
1. Value swap: Bob buys datatokens from marketplace
1. Bob uses a service he just purchased (download)

Let's go through each step.

## 0. Installation

If you haven't installed yet:
```console
pip install ocean-lib
```

## 1. Initialize services

This quickstart treats the publisher service, metadata store, and marketplace as 
externally-run services. For convenience, we run them locally in default settings.

```
docker run @oceanprotocol/provider-py:latest
docker run @oceanprotocol/metadatastore:latest
docker run @oceanprotocol/marketplace:latest
```

## 2. Alice publishes assets for data services (= publishes a datatoken contract)

```python
from ocean_lib import Ocean
from ocean_lib.web3_internal.utils import get_account
from ocean_lib.models.metadata_example import METADATA_EXAMPLE

#Alice's config
config = {
   'network' : 'rinkeby',
   'privateKey' :'8da4ef21b864d2cc526dbdb2a120bd2874c36c9d0a1fb7f8c63d7f7a8b41de8f',
   'metadataStoreUri' : 'localhost:5000',
   'providerUri' : 'localhost:8030'
}
ocean = Ocean(config)
account = get_account(0)

data_token = ocean.create_data_token(ocean.config.metadata_store_url, account)
token_address = data_token.address

# `ocean.assets.create` will encrypt the URLs using the provider's encrypt service endpoint and update 
# the asset before pushing to metadata store
# `ocean.assets.create` will require that token_address is a valid DataToken contract address, unless token_address
# is not provided then the `create` method will first create a new data token and use it in the new
# asset.
asset = ocean.assets.create(METADATA_EXAMPLE, account, data_token_address=token_address)
assert token_address == asset._other_values['dataTokenAddress']

did = asset.did
```

## 3. Alice mints 100 tokens

```python
data_token.mint(account.address, 100, account)
```

## 4. Alice allows marketplace to sell her datatokens

```python
marketplace_address = '0x068ed00cf0441e4829d9784fcbe7b9e26d4bd8d0'
data_token.approve(marketplace_address, 20)
```

## 5. Marketplace posts asset for sale
Now, you're the marketplace:)

```python
from ocean_lib import Ocean

#Market's config
config = {
   'network': 'rinkeby',
   'privateKey':'1234ef21b864d2cc526dbdb2a120bd2874c36c9d0a1fb7f8c63d7f7a8b41de8f',
}
market_ocean = Ocean(config)

asset = ocean.assets.resolve(did)
service1 = asset.get_service('download')
service2 = asset.get_service('access')
price = 10.0 #marketplace-set price of 10 USD / datatoken

#Display key asset information, such as the cost of each service
print(f"Service 1 costs {service1.get_num_dt_needed() * price} USD") # 1.5 * 10 = 15
print(f"Service 2 costs {service2.get_num_dt_needed() * price} USD") # 2.5 * 10 = 25
```

## 6. Value swap: Bob buys datatokens from marketplace

```python
#Not shown: in marketplace GUI, Bob uses Stripe to send USD to marketplace (or other methods / currencies).

market_token = market_ocean.get_data_token(token_address)
market_token.transfer(dst_address=bob_address, 1.0)
```
   
## 7. Bob uses a service he just purchased (download)
Now, you're Bob:)

```python

#Bob's config
config = {
   'network': 'rinkeby',
   'privateKey':'1234ef21b864d2cc526dbdb2a120bd2874c36c9d0a1fb7f8c63d7f7a8b41de8o',
}
market_ocean = Ocean(config)

service = asset.get_service('access')
file_path = bob_ocean.assets.download(asset.did, service.index, bob_account, '~/my-datasets')
```
