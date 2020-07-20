#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

from ocean_lib import Ocean
from ocean_lib.ocean.util import toBase18
from ocean_lib.web3_internal.utils import get_account
from ocean_lib.web3_internal.wallet import Wallet

def test_simple_flow():

    alice_account = get_account(0)
    alice_address = alice_account.address
    bob_account = get_account(1)
    bob_address = bob_account.address
    dataset_download_endpoint = 'http://localhost:8030/api/v1/services'
    _config = ConfigProvider.get_config()
    # 1. Alice publishes a dataset (= publishes a datatoken)
    config = {'network': _config.network_url,
              'dtfactory.address': _config.dtfactory_address
    ocean = Ocean(config)
    alice_wallet = Wallet(ocean.web3, key=alice_account.private_key)
    token = ocean.create_data_token(dataset_download_endpoint, alice_wallet)
    dt_address = token.address

    # 3. Alice mints 100 datatokens
    token.mint(alice_address, 100.0, alice_wallet)

    # 4. Alice transfers 1 datatoken to Bob
    token.transfer(bob_address, 1.0, alice_wallet)

    # 5. Bob consumes dataset. This includes payment to the provider (Alice)
    bob_ocean = Ocean(config)
    bob_wallet = Wallet(bob_ocean.web3, key=bob_account.private_key)
    token = bob_ocean.get_data_token(dt_address)
    (tx_id, _) = token.transfer(alice_account.address, toBase18(1.0), bob_wallet)
    _file = token.download(tx_id, '/tmp', consumer_address=bob_account.address)
    assert _file and _file.startswith('/tmp') and len(_file) > len('/tmp')
