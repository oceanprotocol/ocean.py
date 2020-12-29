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


alice_wallet = Wallet(ocean.web3, private_key=os.getenv('MY_TEST_KEY'))

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




pool = ocean.pool.create(
   token_address,
   data_token_amount=100.0,
   OCEAN_amount=5.0,
   from_wallet=alice_wallet
)

pool_address = pool.address
print(f'DataToken @{data_token.address} has a `pool` available @{pool_address}')
