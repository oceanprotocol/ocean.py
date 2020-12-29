import os
from ocean_lib.ocean.util import to_base_18
from ocean_lib.web3_internal.wallet import Wallet

bob_wallet = Wallet(ocean.web3, private_key=os.getenv('Publisher_Key'))
data_token = market_ocean.get_data_token(token_address)

market_ocean.pool.buy_data_tokens(
    pool_address, 
    amount=1.0, # buy one data token
    max_OCEAN_amount=price_in_OCEAN+0.1, # pay maximum 0.1 OCEAN tokens
    from_wallet=bob_wallet
)

print(f'bob has {data_token.token_balance(bob_wallet.address)} datatokens.')

quote = ocean.assets.order(asset.did, bob_wallet.address, service_index=service.index)
order_tx_id = market_ocean.assets.pay_for_service(
    quote.amount, quote.data_token_address, asset.did, service.index, market_address, bob_wallet
)