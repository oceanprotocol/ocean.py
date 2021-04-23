#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""isort:skip_file"""

import uuid
import os
import json

import pytest
from ocean_lib.config_provider import ConfigProvider

# Setup ocean_lib.enforce_typing_shim before importing anything that uses it
from ocean_lib.enforce_typing_shim import setup_enforce_typing_shim

setup_enforce_typing_shim()

from ocean_lib.example_config import ExampleConfig  # noqa: E402
from ocean_lib.ocean.util import get_web3_connection_provider, to_base_18  # noqa: E402
from ocean_lib.web3_internal.contract_handler import ContractHandler  # noqa: E402
from ocean_lib.web3_internal.web3_provider import Web3Provider  # noqa: E402
from ocean_lib.web3_internal.web3helper import Web3Helper  # noqa: E402
from tests.resources.ddo_helpers import get_metadata  # noqa: E402
from tests.resources.helper_functions import (  # noqa: E402
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

    network = Web3Helper.get_network_name()
    wallet = get_ganache_wallet()
    addresses_file = config.address_file

    if os.path.exists(addresses_file):
        with open(addresses_file) as f:
            network_addresses = json.load(f)
    else:
        network_addresses = {network: {}}

    if network not in network_addresses:
        network = "development"

    if network in ["ganache", "development"] and wallet:

        print(
            f"sender: {wallet.key}, {wallet.address}, {wallet.password}, {wallet.keysStr()}"
        )
        print(
            f"sender balance: {Web3Helper.from_wei(Web3Helper.get_ether_balance(wallet.address))}"
        )
        assert Web3Helper.from_wei(Web3Helper.get_ether_balance(wallet.address)) > 10

        from ocean_lib.models.data_token import DataToken

        OCEAN_token = DataToken(address=network_addresses[network]["Ocean"])
        amt_distribute = 1000
        amt_distribute_base = to_base_18(float(amt_distribute))
        for w in (get_publisher_wallet(), get_consumer_wallet()):
            if Web3Helper.from_wei(Web3Helper.get_ether_balance(w.address)) < 2:
                Web3Helper.send_ether(wallet, w.address, 4)

            if OCEAN_token.token_balance(w.address) < 100:
                OCEAN_token.transfer(w.address, amt_distribute_base, from_wallet=wallet)


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
    metadata["main"]["files"][0]["checksum"] = str(uuid.uuid4())
    return metadata
