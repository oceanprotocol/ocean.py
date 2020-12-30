import os

from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_utils.agreements.service_factory import ServiceDescriptor
#Publish asset to download. Tetsing
#Alice's config
config = {
   'network' : os.getenv('NETWORK_URL'),
   'metadataStoreUri' : os.getenv('AQUARIUS_URL'),
   'providerUri' : os.getenv('PROVIDER_URL'),
}
ocean = Ocean(config)


alice_wallet = Wallet(ocean.web3, private_key=os.getenv('Publisher_Key'))

data_token = ocean.create_data_token('GPT-2 Pretrained', 'GPT2P', alice_wallet, blob=ocean.config.metadata_store_url)
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
        "license": "CC0: Public Domain", "dateCreated": 2020-12-10, 
        "files": [
            { "index": 0, "contentType": "application/zip", "url": "https://s3.amazonaws.com/datacommons-seeding-us-east/10_Monkey_Species_Small/assets/training.zip"},
            { "index": 1, "contentType": "application/binary", "url": "https://s3://transformers-bucket/Models/pytorch_model.bin"},
            { "index": 2, "contentType": "application/zip", "url": "https://s3.amazonaws.com/datacommons-seeding-us-east/10_Monkey_Species_Small/assets/validation.zip"}]}
}

#ocean.assets.create will encrypt URLs using Provider's encrypt service endpoint, and update asset before putting on-chain.
#It requires that token_address is a valid DataToken contract address. If that isn't provided, it will create a new token.
asset = ocean.assets.create(metadata, alice_wallet, service_descriptors=[download_service], data_token_address=token_address)
assert token_address == asset.data_token_address

did = asset.did  # did contains the datatoken address

data_token.mint_tokens(alice_wallet.address, 100.0, alice_wallet)


pool = ocean.pool.create(
   token_address,
   data_token_amount=100.0,
   OCEAN_amount=5.0,
   from_wallet=alice_wallet
)

pool_address = pool.address
print(f'DataToken @{data_token.address} has a `pool` available @{pool_address}')


export AWS_ACCESS_KEY_ID=AKIASP2W343KRYPPN4U4
export AWS_SECRET_ACCESS_KEY='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'
export AWS_DEFAULT_REGION=us-west-2