from ocean_lib.data_provider.data_service_provider import DataServiceProviderfrom ocean_lib.data_provider.data_service_provider import DataServiceProviderfrom ocean_lib.data_provider.data_service_provider import DataServiceProviderfrom ocean_lib.data_provider.data_service_provider import DataServiceProvider# Quickstart: Marketplace Flow

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
docker run @oceanprotocol/aquarius:latest
docker run @oceanprotocol/marketplace:latest
```

## 2. Alice publishes assets for data services (= publishes a DataToken contract)

```python
from ocean_utils.agreements.service_factory import ServiceDescriptor

from ocean_lib.ocean import Ocean
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.web3_internal.web3helper import Web3Helper
from ocean_lib.data_provider.data_service_provider import DataServiceProvider

#Alice's config
config = {
   'network' : 'rinkeby',
   'metadataStoreUri' : 'localhost:5000',
   'providerUri' : 'localhost:8030'
}
ocean = Ocean(config)
alice_wallet = Wallet(ocean.web3, private_key='8da4ef21b864d2cc526dbdb2a120bd2874c36c9d0a1fb7f8c63d7f7a8b41de8f')

data_token = ocean.create_data_token(ocean.config.metadata_store_url, alice_wallet)
token_address = data_token.address

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
            "cost": Web3Helper.to_wei(1.5), # service cost is 1.5 tokens, must be converted to 
            "timeout": 3600 * 24,
            "datePublished": metadata["main"]['dateCreated']
        }
    }

service_endpoint = DataServiceProvider.get_download_endpoint(ocean.config)
download_service = ServiceDescriptor.access_service_descriptor(service_attributes, service_endpoint)
asset = ocean.assets.create(metadata, alice_wallet, service_descriptors=[download_service], data_token_address=token_address)
assert token_address == asset.data_token_address

did = asset.did
```

## 3. Alice mints 100 tokens

```python

alice_wallet = Wallet()  # From step 2
data_token = DataToken()  # From step 2
data_token.mint_tokens(alice_wallet.address, 100.0, alice_wallet)
```

## 4. Alice allows marketplace to sell her datatokens

```python
data_token = DataToken()  # From step 2
marketplace_address = '0x068ed00cf0441e4829d9784fcbe7b9e26d4bd8d0'
data_token.approve_tokens(marketplace_address, 20.0)
```

## 5. Marketplace posts asset for sale
Now, you're the marketplace:)

```python
from ocean_utils.agreements.service_types import ServiceTypes

from ocean_lib.ocean import Ocean
from ocean_lib.web3_internal.web3helper import Web3Helper

#Market's config
config = {
   'network': 'rinkeby',
}
market_ocean = Ocean(config)

did = ''  # from step 2
asset = market_ocean.assets.resolve(did)
service1 = asset.get_service(ServiceTypes.ASSET_ACCESS)
price = 10.0  # marketplace-set price of 10 USD / datatoken

# Display key asset information, such as the cost of each service
tokens_amount = Web3Helper.from_wei(service1.get_cost())
print(f"Service 1 costs {tokens_amount * price} USD") # 1.5 * 10 = 15
```

## 6. Value swap: Bob buys datatokens from marketplace

```python
# Not shown: in marketplace GUI, Bob uses Stripe to send USD to marketplace (or other methods / currencies).

data_token = market_ocean.get_data_token(token_address)
data_token.transfer_tokens(dst_address=bob_address, 1.0)
```
   
## 7. Bob uses a service he just purchased (download)
Now, you're Bob:)

```python

# Bob's config
config = {
   'network': 'rinkeby',
}
bob_ocean = Ocean(config)

bob_wallet = Wallet(bob_ocean.web3, private_key='1234ef21b864d2cc526dbdb2a120bd2874c36c9d0a1fb7f8c63d7f7a8b41de8o')
service = asset.get_service(ServiceTypes.ASSET_ACCESS)
quote = bob_ocean.assets.order(asset.did, bob_wallet.address, service_index=service.index)
bob_ocean.assets.pay_for_service(quote.amount, quote.data_token_address, quote.receiver_address, bob_wallet)
file_path = bob_ocean.assets.download(asset.did, service.index, bob_wallet, '~/my-datasets')
```
