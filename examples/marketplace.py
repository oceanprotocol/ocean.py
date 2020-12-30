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

#did='did:op:2cbDb0Aaa1F546829E31267d1a7F74d926Bb5B1B'  # from step 3
#pool_address = '0xeaD638506951B4a4c3575bbC0c7D1491c17B7A08'  # from step 4
asset = market_ocean.assets.resolve(did)
service1 = asset.get_service(ServiceTypes.ASSET_ACCESS)
pool = market_ocean.pool.get(pool_address)
#token_address = '0x2cbDb0Aaa1F546829E31267d1a7F74d926Bb5B1B'

OCEAN_address = market_ocean.pool.ocean_address
price_in_OCEAN = ocean.pool.calcInGivenOut(
    pool_address, OCEAN_address, token_address, token_out_amount=1.0
)
print(f"Price of 1 datatoken is {price_in_OCEAN} OCEAN")

import os
from ocean_lib.ocean.util import to_base_18
from ocean_lib.web3_internal.wallet import Wallet

bob_wallet = Wallet(ocean.web3, private_key=os.getenv('Consumer_Key'))
data_token = market_ocean.get_data_token(token_address)

market_ocean.pool.buy_data_tokens(
    pool_address, 
    amount=1.0, # buy one data token
    max_OCEAN_amount=price_in_OCEAN, # pay maximum 0.1 OCEAN tokens
    from_wallet=bob_wallet
)

print(f'bob has {data_token.token_balance(bob_wallet.address} datatokens.')