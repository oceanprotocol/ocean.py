#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import uuid

import pytest

from ocean_lib import ConfigProvider
from ocean_lib.config import NAME_DATA_TOKEN_FACTORY_ADDRESS
from ocean_lib.web3_internal import Web3Helper
from ocean_lib.web3_internal.account import Account
from ocean_lib.web3_internal.contract_handler import ContractHandler
from ocean_lib.web3_internal.web3_provider import Web3Provider

from examples import ExampleConfig
from ocean_lib.ocean.util import get_web3_provider
from tests.resources.helper_functions import (
    get_metadata,
    setup_logging,
    get_publisher_ocean_instance, get_consumer_ocean_instance, get_publisher_account, get_consumer_account, new_factory_contract)

setup_logging()


@pytest.fixture(autouse=True)
def setup_all():
    config = ExampleConfig.get_config()
    ConfigProvider.set_config(config)
    Web3Provider.init_web3(provider=get_web3_provider(config.network_url))
    ContractHandler.set_artifacts_path(config.artifacts_path)

    factory_contract = new_factory_contract()
    config.set('eth-network', NAME_DATA_TOKEN_FACTORY_ADDRESS, factory_contract.address)

    web3 = Web3Provider.get_web3()
    if web3.eth.accounts and web3.eth.accounts[0].lower() == '0xe2DD09d719Da89e5a3D0F2549c7E24566e947260'.lower():
        account = Account(web3.eth.accounts[0], private_key='0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58')

        provider = get_publisher_account()
        if Web3Helper.from_wei(Web3Helper.get_ether_balance(provider.address)) < 10:
            Web3Helper.send_ether(account, provider.address, 25)

        consumer = get_consumer_account()
        if Web3Helper.from_wei(Web3Helper.get_ether_balance(consumer.address)) < 10:
            Web3Helper.send_ether(account, consumer.address, 25)


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
