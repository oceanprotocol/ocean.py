#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import uuid

import pytest

from ocean_lib.config_provider import ConfigProvider
from ocean_lib.web3_internal.web3helper import Web3Helper
from ocean_lib.web3_internal.contract_handler import ContractHandler
from ocean_lib.web3_internal.web3_provider import Web3Provider

from examples import ExampleConfig
from ocean_lib.ocean.util import get_web3_connection_provider
from tests.resources.helper_functions import (
    get_metadata,
    setup_logging,
    get_publisher_ocean_instance,
    get_consumer_ocean_instance,
    get_publisher_wallet,
    get_consumer_wallet,
    get_ganache_wallet)

setup_logging()


@pytest.fixture(autouse=True)
def setup_all():
    config = ExampleConfig.get_config()
    ConfigProvider.set_config(config)
    Web3Provider.init_web3(provider=get_web3_connection_provider(config.network_url))
    ContractHandler.set_artifacts_path(config.artifacts_path)

    network = Web3Helper.get_network_name()
    wallet = get_ganache_wallet()
    if network in ['ganache', 'development'] and wallet:

        print(f'sender: {wallet.key}, {wallet.address}, {wallet.password}, {wallet.keysStr()}')
        print(f'sender balance: {Web3Helper.from_wei(Web3Helper.get_ether_balance(wallet.address))}')
        assert Web3Helper.from_wei(Web3Helper.get_ether_balance(wallet.address)) > 50

        for w in (get_publisher_wallet(), get_consumer_wallet()):
            if Web3Helper.from_wei(Web3Helper.get_ether_balance(w.address)) < 2:
                Web3Helper.send_ether(wallet, w.address, 4)


@pytest.fixture
def publisher_ocean_instance():
    return get_publisher_ocean_instance()


@pytest.fixture
def consumer_ocean_instance():
    return get_consumer_ocean_instance()


@pytest.fixture
def web3_instance():
    config = ExampleConfig.get_config()
    return Web3Provider.get_web3(config.network_url)


@pytest.fixture
def metadata():
    metadata = get_metadata()
    metadata['main']['files'][0]['checksum'] = str(uuid.uuid4())
    return metadata
