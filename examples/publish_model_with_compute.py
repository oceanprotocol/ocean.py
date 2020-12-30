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


def main(did, pool_address, order_tx_id=None):
        ocean = Ocean(config=Config(options_dict=get_config_dict()))
        publisher = Wallet(ocean.web3, private_key='0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58')  # 0xe2DD09d719Da89e5a3D0F2549c7E24566e947260
        #consumer = Wallet(ocean.web3, private_key='0x9bf5d7e4978ed5206f760e6daded34d657572bd49fa5b3fe885679329fb16b16')  # 0x068Ed00cF0441e4829D9784fCBe7b9e26D4BD8d0
        publisher_wallet = Wallet(ocean.web3, private_key=os.getenv('Publisher_Key')) #addr: 0xc966Ba2a41888B6B4c5273323075B98E27B9F364
        consumer = Wallet(ocean.web3, private_key=os.getenv('Consumer_Key')) #addr: 0xEF5dc33A53DD2ED3F670B53F07cEc5ADD4D80504
        pool_address=''
        did=''
        if not (did and pool_address):
            metadata_file = './examples/data/metadata_original_model.json' #GPT-2 Pretrained Meta Data
            with open(metadata_file) as f:
                metadata = json.load(f)

            asset, pool = publish_asset(metadata, publisher_wallet)
            #Dataset asset created successfully: did=did:op:784Cc17176533cc962cf659B9f49349ba6F9df3b, datatoken=0x784Cc17176533cc962cf659B9f49349ba6F9df3b
            #pool_address = 0x3490DDd035B2e1DA30Af09AB6090Bf71fdb94898
        else:
            asset = ocean.assets.resolve(did)
            pool = BPool(pool_address)

        if not asset:
            print(f'publish asset failed, cannot continue with running compute.')
            return
#Bob Consumes Service
#Testing code
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
algo_file = './examples/data/Algo_eval_wikitext.py'
job_id, status = run_compute(asset.did, consumer, algo_file, pool.address, order_tx_id)
print(f'Compute started on asset {asset.did}: job_id={job_id}, status={status}')


'''INFO:ocean:Asset/ddo published on-chain successfully.
Dataset asset created successfully: did=did:op:57Db8282e93Cd7Db6A274EBCf531255F4DDB2e2c, datatoken=0x57Db8282e93Cd7Db6A274EBCf531255F4DDB2e2c
BPool.newBPool(). Begin.
  pool_address = 0x81DDfDe8893b86bC24e04b0aae02Bd087a548E68
BFactory.newBPool(). Done.
datatoken liquidity pool was created at address 0x81DDfDe8893b86bC24e04b0aae02Bd087a548E68
Asset did:op:57Db8282e93Cd7Db6A274EBCf531255F4DDB2e2c can now be purchased from pool @0x81DDfDe8893b86bC24e04b0aae02Bd087a548E68 at the price of 0.5640157924421884 OCEAN tokens.'''