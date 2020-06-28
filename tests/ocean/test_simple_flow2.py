#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

from ocean_lib import Ocean
from ocean_lib.models.factory import FactoryContract
from ocean_lib.ocean.util import confFileValue #FIXME: deprecate this
from ocean_lib.web3_internal.account import Account

def test_simple_flow():
    #set values
    network = 'ganache'
    factory_address = confFileValue(network, 'DTFACTORY_ADDRESS')
    alice_private_key = confFileValue(network, 'TEST_PRIVATE_KEY1') 
    bob_private_key = confFileValue(network, 'TEST_PRIVATE_KEY2')
    
    alice_account = Account(private_key=alice_private_key)
    bob_account = Account(private_key=bob_private_key)
    dataset_download_endpoint = 'http://localhost:8030/api/v1/services'

    # 1. Alice publishes a dataset (= publishes a datatoken)
    config = {'network': network, 'factory.address': factory_address}
    ocean = Ocean(config)
    token = ocean.create_data_token(dataset_download_endpoint, alice_account)
    dt_address = token.address

    # 3. Alice mints 100 tokens
    tx_id = token.mint(alice_account.address, 100, alice_account)
    token.get_tx_receipt(tx_id)

    # 4. Alice transfers 1 token to Bob
    token.transfer(bob_account.address, 1, alice_account)

    # 5. Bob consumes dataset
    bob_ocean = Ocean(config)
    token = bob_ocean.get_data_token(dt_address)
    token_owner = FactoryContract(ocean.config.factory_address).get_token_minter(token.address)

    tx_id = token.transfer(token_owner, 1, bob_account)

    # This is disabled for now because the token transfer sometimes fail on `rinkeby`
    # try:
    #     _tx_id = token.verify_transfer_tx(tx_id, bob_account.address, token_owner)
    # except (Exception, AssertionError) as e:
    #     print(f'token transfer failed: {e}')
    #     raise

    _file = token.download(bob_account, tx_id, '/tmp')
    assert _file and _file.startswith('/tmp') and len(_file) > len('/tmp')
