#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

from ocean_lib import Ocean
from ocean_lib.models.dtfactory import DTFactory
from ocean_lib.ocean.util import confFileValue, toBase18
from ocean_lib.web3_internal.utils import get_account

def test_simple_flow():
    #set values
    network = 'ganache'
    dtfactory_address = confFileValue(network, 'DTFACTORY_ADDRESS')
    
    alice_account = get_account(0)
    alice_address = alice_account.address
    bob_account = get_account(1)
    dataset_download_endpoint = 'http://localhost:8030/api/v1/services'

    # 1. Alice publishes a dataset (= publishes a datatoken)
    config = {'network': network, 'dtfactory.address': dtfactory_address}
    ocean = Ocean(config)
    token = ocean.create_data_token(dataset_download_endpoint, alice_account)
    dt_address = token.address

    # 3. Alice mints 100 tokens
    tx_id = token.mint(alice_account.address, toBase18(100.0), alice_account)
    #token.get_tx_receipt(tx_id)

    # 4. Alice transfers 1 token to Bob
    token.transfer(bob_account.address, toBase18(1.0), alice_account)

    # 5. Bob consumes dataset
    bob_ocean = Ocean(config)
    token = bob_ocean.get_data_token(dt_address)
    #minter_address = DTFactory(ocean.config.factory_address).get_token_minter(token.address)
    minter_address = alice_address #the above returns None, so do this for now
    tx_id = token.transfer(minter_address, toBase18(1.0), bob_account)

    #FIXME: uncomment and make this work
    _file = token.download(bob_account, tx_id, '/tmp')
    assert _file and _file.startswith('/tmp') and len(_file) > len('/tmp')
