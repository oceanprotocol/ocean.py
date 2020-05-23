# Quickstart: Marketplace Flow

This batteries-included flow includes metadata, multiple services for one datatoken, and compute-to-data.

It focuses on Alice's experience as a publisher, and Bob's experience as a buyer & consumer. The rest are services used by Alice and Bob.

Here's the steps.
1. Initialize services
1. Alice publishes assets for data services (= publishes a datatoken contract)
1. Alice mints 100 tokens
1. Alice allows marketplace to sell her datatokens
1. Bob buys datatokens from marketplace
1. Bob uses a service he just purchased (compute-to-data)

Let's go through each step.

## 0. Installation

If you haven't installed yet:
```console
pip install ocean-lib
```

## 1. Initialize services

This quickstart treats the publisher service, metadata store, and marketplace as externally-run services. For convenience, we run them locally in default settings.

```
docker run @oceanprotocol/provider-py:latest
docker run @oceanprotocol/metadatastore:latest
docker run @oceanprotocol/marketplace:latest
```

## 2. Alice publishes assets for data services (= publishes a datatoken contract)

For now, you're Alice:) Let's proceed.


```python
import ocean_lib as ocean

#Alice's config
config = {
   'network' : 'rinkeby',
   'private_key' :'8da4ef21b864d2cc526dbdb2a120bd2874c36c9d0a1fb7f8c63d7f7a8b41de8f',
   'metadataStoreURI' : 'localhost:5000',
   'providerUri' : 'localhost:8030'
}
ocean = ocean.Ocean(alice_config)
account = ocean.accounts.list()[0]

token = ocean.datatoken.create(config.metadataStoreURI, account)

dt_address = token.getAddress()

#create asset
metadata={
   'did'  : 'did:op:1234',
   'owner' : '0xaaaaa',
   'dtAddress' : dt_address,
   'name' : 'Asset1',
   'services' = [
      {  'id':0, 'serviceEndpoint':'providerUri', 'type':'download', 'dtCost':10, 'timeout':0,
         'files':[{'url':'http://example.net'},{'url':'http://example.com' }]
      },
      { 'id':1, 'type':'compute', 'serviceEndpoint':'providerUri', 'dtCost':1,'timeout':3600},
      { 'id':2,   'type':'compute',  'serviceEndpoint':'providerUri',  'dtCost':2, 'timeout':7200 },
   ]
}

#create will encrypt the URLs using publisher and update the ddo before pushing to metadata store
#create will require that metadata.dtAddress is a valid DT Contract address
asset = ocean.assets.create(metadata, account)
did = asset.did
```

## 3. Alice mints 100 tokens

```python
token.mint(100)
```

## 3. Alice allows marketplace to sell her datatokens

```python
marketplace_address = '0x9876'
token.approve(marketplace_address, 20)
```

## 4. Bob buys datatokens from marketplace

Now, you are Bob :)

```
bob_config = {
   'network' : 'rinkeby',
   'privateKey' : '1234ef21b864d2cc526dbdb2a120bd2874c36c9d0a1fb7f8c63d7f7a8b41de8f'  
   'marketPlaceUri' : 'localhost:3000'
}
bob_ocean = ocean.Ocean(bob_config)
bob_account = bob_ocean.accounts.list()[0]

asset = ocean.assets.resolve(did)
service_index = asset.findServiceByType('compute')
num_dt_needed = assets.getDtCost(service_index)

(price, currency) = ocean.marketplace.getPrice(num_dt_needed,asset.dtAddress)
bob_account.approve(price, currency, marketplace_address)
ocean.marketplace.buy(num_dt_needed, asset.dtAddress)
```

## 5. Bob uses a service he just purchased (compute-to-data)

```python

service_index = assets.findServiceByType('compute')

raw_algo_meta = {
  'rawcode' : 'console.log("Hello world"!)',
  'format' : 'docker-image',
  'version' : '0.1',
  'container' : {'entrypoint':'node $ALGO','image':'node','tag' : '10'},
}

compute_job = asset.StartCompute(service_index, raw_algo_meta, account)
FIXME grab results of compute
```
