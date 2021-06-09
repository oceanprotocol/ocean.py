#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import os
import uuid

import pytest
from ocean_lib.common.aquarius.aquarius_provider import AquariusProvider
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.util import get_web3_connection_provider
from ocean_lib.web3_internal.contract_handler import ContractHandler
from ocean_lib.web3_internal.currency import from_wei, to_wei
from ocean_lib.web3_internal.transactions import send_ether
from ocean_lib.web3_internal.utils import get_ether_balance
from ocean_lib.web3_internal.web3_provider import Web3Provider
from tests.resources.ddo_helpers import get_metadata
from tests.resources.helper_functions import (
    get_consumer_ocean_instance,
    get_consumer_wallet,
    get_ganache_wallet,
    get_publisher_ocean_instance,
    get_publisher_wallet,
    setup_logging,
)

setup_logging()


@pytest.fixture(autouse=True)
def setup_all(request):
    # a test can skip setup_all() via decorator "@pytest.mark.nosetup_all"
    if "nosetup_all" in request.keywords:
        return
    config = ExampleConfig.get_config()
    ConfigProvider.set_config(config)
    Web3Provider.init_web3(provider=get_web3_connection_provider(config.network_url))
    ContractHandler.set_artifacts_path(config.artifacts_path)

    wallet = get_ganache_wallet()

    if not wallet:
        return

    addresses_file = config.address_file
    if not os.path.exists(addresses_file):
        return

    with open(addresses_file) as f:
        network_addresses = json.load(f)

    print(
        f"sender: {wallet.key}, {wallet.address}, {wallet.password}, {wallet.keys_str()}"
    )
    print(f"sender balance: {from_wei(get_ether_balance(wallet.address))}")
    assert (
        from_wei(get_ether_balance(wallet.address)) > 10
    ), "Ether balance less than 10."

    from ocean_lib.models.data_token import DataToken

    OCEAN_token = DataToken(address=network_addresses["development"]["Ocean"])

    amt_distribute = 1000
    amt_distribute_in_wei = to_wei(amt_distribute)

    for w in (get_publisher_wallet(), get_consumer_wallet()):
        if from_wei(get_ether_balance(w.address)) < 2:
            send_ether(wallet, w.address, 4)

        if OCEAN_token.token_balance(w.address) < 100:
            OCEAN_token.mint(wallet.address, amt_distribute_in_wei, from_wallet=wallet)
            OCEAN_token.transfer(w.address, amt_distribute_in_wei, from_wallet=wallet)


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
def aquarius_instance():
    config = ExampleConfig.get_config()
    return AquariusProvider.get_aquarius(config.metadata_cache_uri)


@pytest.fixture
def metadata():
    metadata = get_metadata()
    metadata["main"]["files"][0]["checksum"] = str(uuid.uuid4())
    return metadata
