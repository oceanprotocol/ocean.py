import os
from ocean_lib.ocean.util import to_base_18
from ocean_lib.web3_internal.wallet import Wallet

#Download asset. For testing purpooses

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

file_path = ocean.assets.download(
    asset.did, 
    service.index, 
    bob_wallet, 
    order_tx_id, 
    destination='./my-datasets'
)
from_wallet=w3.toChecksumAddress(bob_wallet.address)
tx_hash = dt.startOrder(from_wallet, amount_base, service.index, market_address, from_wallet)
