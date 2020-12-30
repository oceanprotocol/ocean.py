import os

from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_utils.agreements.service_factory import ServiceDescriptor
import json

from ocean_utils.agreements.service_types import ServiceTypes
from ocean_utils.utils.utilities import get_timestamp

from ocean_lib.config import Config
from ocean_lib.models.algorithm_metadata import AlgorithmMetadata
from ocean_lib.models.bpool import BPool
from ocean_lib.models.data_token import DataToken
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.wallet import Wallet
import os

from examples.compute_service import build_compute_descriptor, get_config_dict, run_compute, publish_asset
#Publish Model with compute to data, with training algorithim
#Alice's config
config = {
   'network' : os.getenv('NETWORK_URL'),
   'metadataStoreUri' : os.getenv('AQUARIUS_URL'),
   'providerUri' : os.getenv('PROVIDER_URL'),
}
ocean = Ocean(config)


alice_wallet = Wallet(ocean.web3, private_key=os.getenv('Publisher_Key'))

data_token = ocean.create_data_token('DToxen2', 'DTX2', alice_wallet, blob=ocean.config.metadata_store_url)
token_address = data_token.address

date_created = "2020-02-01T10:55:11Z"
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

metadata =  {
    "main": {
        "type": "dataset", "name": "PreTrained GPT-2 Model", "author": "Posthuman", 
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



pool = ocean.pool.create(
   token_address,
   data_token_amount=100.0,
   OCEAN_amount=5.0,
   from_wallet=alice_wallet
)

pool_address = pool.address
print(f'DataToken @{data_token.address} has a `pool` available @{pool_address}')

def main(did, pool_address, order_tx_id=None):
    ocean = Ocean(config=Config(options_dict=get_config_dict()))
publisher = Wallet(ocean.web3, private_key='0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58')  # 0xe2DD09d719Da89e5a3D0F2549c7E24566e947260
#consumer = Wallet(ocean.web3, private_key='0x9bf5d7e4978ed5206f760e6daded34d657572bd49fa5b3fe885679329fb16b16')  # 0x068Ed00cF0441e4829D9784fCBe7b9e26D4BD8d0
publisher_wallet = Wallet(ocean.web3, private_key=os.getenv('Publisher_Key')) #addr: 0xc966Ba2a41888B6B4c5273323075B98E27B9F364
consumer = Wallet(ocean.web3, private_key=os.getenv('Consumer_Key')) #addr: 0xEF5dc33A53DD2ED3F670B53F07cEc5ADD4D80504

        if not (did and pool_address):
            metadata_file = './examples/data/metadata.json'
            with open(metadata_file) as f:
                metadata = json.load(f)

            asset, pool = publish_asset(metadata, publisher)
            #Dataset asset created successfully: did=did:op:784Cc17176533cc962cf659B9f49349ba6F9df3b, datatoken=0x784Cc17176533cc962cf659B9f49349ba6F9df3b
            #pool_address = 0x3490DDd035B2e1DA30Af09AB6090Bf71fdb94898
        else:
            asset = ocean.assets.resolve(did)
            pool = BPool(pool_address)

        if not asset:
            print(f'publish asset failed, cannot continue with running compute.')
            return
#Bob Consumes Service

bob_wallet = Wallet(ocean.web3, private_key=os.getenv('Consumer_Key'))
data_token = market_ocean.get_data_token(token_address)

market_ocean.pool.buy_data_tokens(
    pool_address, 
    amount=1.0, # buy one data token
    max_OCEAN_amount=price_in_OCEAN+0.1, # with buffer
    from_wallet=bob_wallet
)



print(f'bob has {data_token.token_balance(bob_wallet.address)} datatokens.')

quote = ocean.assets.order(asset.did, bob_wallet.address, service_index=service.index)
order_tx_id = market_ocean.assets.pay_for_service(
    quote.amount, quote.data_token_address, asset.did, service.index, market_address, bob_wallet
)
print(f'Requesting compute using asset {asset.did} and pool {pool.address}')
algo_file = './examples/data/algorithm.py'
job_id, status = run_compute(asset.did, consumer, algo_file, pool.address, order_tx_id)
print(f'Compute started on asset {asset.did}: job_id={job_id}, status={status}')
