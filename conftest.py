#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import os
import uuid

import pytest

from ocean_lib.common.aquarius.aquarius_provider import AquariusProvider
from ocean_lib.models.v4.erc20_token import ERC20Token
from ocean_lib.models.v4.factory_router import FactoryRouter
from ocean_lib.web3_internal.currency import from_wei, to_wei
from ocean_lib.web3_internal.transactions import send_ether
from ocean_lib.web3_internal.utils import get_ether_balance
from tests.resources.ddo_helpers import get_metadata
from tests.resources.helper_functions import (
    get_address_of_type,
    get_another_consumer_wallet,
    get_consumer_ocean_instance,
    get_consumer_wallet,
    get_example_config,
    get_ganache_wallet,
    get_publisher_ocean_instance,
    get_publisher_wallet,
    get_web3,
    setup_logging,
    get_another_consumer_wallet,
    get_factory_deployer_wallet,
)

_NETWORK = "ganache"

setup_logging()


@pytest.fixture(autouse=True)
def setup_all(request, config, web3):
    # a test can skip setup_all() via decorator "@pytest.mark.nosetup_all"
    if "nosetup_all" in request.keywords:
        return

    wallet = get_ganache_wallet()

    if not wallet:
        return

    addresses_file = config.address_file
    if not os.path.exists(addresses_file):
        return

    with open(addresses_file) as f:
        network_addresses = json.load(f)

    print(f"sender: {wallet.key}, {wallet.address}, {wallet.keys_str()}")
    print(f"sender balance: {from_wei(get_ether_balance(web3, wallet.address))}")
    assert get_ether_balance(web3, wallet.address) >= to_wei(
        10
    ), "Ether balance less than 10."

    OCEAN_token = ERC20Token(web3, address=network_addresses["development"]["Ocean"])

    amt_distribute = to_wei(1000)

    for w in (get_publisher_wallet(), get_consumer_wallet()):
        if get_ether_balance(web3, w.address) < to_wei(2):
            send_ether(wallet, w.address, to_wei(4))

        if OCEAN_token.balanceOf(w.address) < to_wei(100):
            OCEAN_token.transfer(w.address, amt_distribute, from_wallet=wallet)


@pytest.fixture
def config():
    return get_example_config()


@pytest.fixture
def publisher_ocean_instance():
    return get_publisher_ocean_instance()


@pytest.fixture
def consumer_ocean_instance():
    return get_consumer_ocean_instance()


@pytest.fixture
def web3():
    return get_web3()


@pytest.fixture
def aquarius_instance(config):
    return AquariusProvider.get_aquarius(config.metadata_cache_uri)


@pytest.fixture
def metadata():
    metadata = get_metadata()
    metadata["main"]["files"][0]["checksum"] = str(uuid.uuid4())
    return metadata


@pytest.fixture
def publisher_wallet():
    return get_publisher_wallet()


@pytest.fixture
def consumer_wallet():
    return get_consumer_wallet()


@pytest.fixture
def another_consumer_wallet():
    return get_another_consumer_wallet()


@pytest.fixture
def factory_deployer_wallet():
    return get_factory_deployer_wallet(_NETWORK)


@pytest.fixture
def factory_router(web3, config):
    return FactoryRouter(
        web3,
        get_address_of_type(config, "Router"),
    )
