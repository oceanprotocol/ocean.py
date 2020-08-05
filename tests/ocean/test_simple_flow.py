#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.ocean import Ocean
from ocean_lib.models.dtfactory import DTFactory

from ocean_lib.web3_internal.web3helper import Web3Helper
from tests.resources.helper_functions import get_publisher_wallet, get_consumer_wallet


def test_simple_flow():
    network = Web3Helper.get_network_name()
    alice_wallet = get_publisher_wallet()
    bob_wallet = get_consumer_wallet()
    dataset_download_endpoint = 'http://localhost:8030/api/v1/services'
    _config = ConfigProvider.get_config()
    # 1. Alice publishes a dataset (= publishes a datatoken)
    config = {
        'network': _config.network_url,
        'factory.address': DTFactory.configured_address(network, _config.address_file),
    }
    ocean = Ocean(config)
    token = ocean.create_data_token(dataset_download_endpoint, alice_wallet)
    dt_address = token.address

    # 3. Alice mints 100 tokens
    tx_id = token.mint_tokens(alice_wallet.address, 100, alice_wallet)
    token.get_tx_receipt(tx_id)

    # 4. Alice transfers 1 token to Bob
    token.transfer_tokens(bob_wallet.address, 1, alice_wallet)

    # 5. Bob consumes dataset
    bob_ocean = Ocean(config)
    token = bob_ocean.get_data_token(dt_address)
    address = DTFactory.configured_address(network, _config.address_file)
    token_owner = DTFactory(address).get_token_minter(token.address)

    tx_id = token.transfer_tokens(token_owner, 1, bob_wallet)

    try:
        _tx_id = token.verify_transfer_tx(tx_id, bob_wallet.address, token_owner)
    except (Exception, AssertionError) as e:
        print(f'token transfer failed: {e}')
        raise

    _file = token.download(bob_wallet, tx_id, '/tmp')
    assert _file and _file.startswith('/tmp') and len(_file) > len('/tmp')
