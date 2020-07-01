#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

from ocean_lib import Ocean
from ocean_lib.models.dtfactory import DTFactory
from ocean_lib.ocean.util import confFileValue, toBase18
from ocean_lib.web3_internal.utils import get_account
from ocean_lib.web3_internal.account import privateKeyToAddress
from ocean_lib.web3_internal.wallet import Wallet

def test_simple_flow():
    #set values
    network = 'ganache'
    dtfactory_address = confFileValue(network, 'DTFACTORY_ADDRESS')
    alice_private_key = get_account(0).private_key
    alice_address = privateKeyToAddress(alice_private_key)
    bob_private_key = get_account(1).private_key
    bob_address = privateKeyToAddress(bob_private_key)
    dataset_download_endpoint = 'http://localhost:8030/api/v1/services'

    # 1. Alice publishes a dataset (= publishes a datatoken)
    config = {'network': network, 'dtfactory.address': dtfactory_address}
    ocean = Ocean(config)
    alice_wallet = Wallet(ocean.web3, key=alice_private_key)
    token = ocean.create_data_token(dataset_download_endpoint, alice_wallet)
    dt_address = token.address

    # 3. Alice mints 100 datatokens
    token.mint(alice_address, toBase18(100.0), alice_wallet)

    # 4. Alice transfers 1 datatoken to Bob
    token.transfer(bob_address, toBase18(1.0), alice_wallet)

    # 5. Bob consumes dataset. This includes payment to the provider (Alice)
    bob_ocean = Ocean(config)
    bob_wallet = Wallet(bob_ocean.web3, key=bob_private_key)
    token = bob_ocean.get_data_token(dt_address)
    (tx_id, _) = token.transfer(alice_address, toBase18(1.0), bob_wallet)
    _file = token.download(tx_id, '/tmp', consumer_address=bob_address)
    assert _file and _file.startswith('/tmp') and len(_file) > len('/tmp')
