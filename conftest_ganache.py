#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from brownie.network import accounts
from web3.main import Web3

from ocean_lib.example_config import get_config_dict
from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.web3_internal.contract_utils import get_contracts_addresses_all_networks
from ocean_lib.web3_internal.utils import connect_to_network
from tests.resources.helper_functions import (
    get_another_consumer_wallet,
    get_consumer_ocean_instance,
    get_consumer_wallet,
    get_factory_deployer_wallet,
    get_file1,
    get_file2,
    get_file3,
    get_ganache_wallet,
    get_provider_wallet,
    get_publisher_ocean_instance,
    get_publisher_wallet,
    setup_logging,
)

_NETWORK = "ganache"

setup_logging()


@pytest.fixture(autouse=True)
def setup_all(request, config, ocean_token):
    connect_to_network("development")
    accounts.clear()

    # a test can skip setup_all() via decorator "@pytest.mark.nosetup_all"
    if "nosetup_all" in request.keywords:
        return

    wallet = get_ganache_wallet()

    if not wallet:
        return

    if not get_contracts_addresses_all_networks(config):
        print("Can not find adddresses.")
        return

    assert accounts.at(wallet.address).balance() >= Web3.toWei(
        "10", "ether"
    ), "Ether balance less than 10."

    amt_distribute = Web3.toWei("1000", "ether")
    ocean_token.mint(wallet.address, Web3.toWei("20000", "ether"), {"from": wallet})

    for w in (get_publisher_wallet(), get_consumer_wallet()):
        if accounts.at(w.address).balance() < Web3.toWei("2", "ether"):
            wallet.transfer(w.address, "4 ether")

        if ocean_token.balanceOf(w.address) < Web3.toWei("100", "ether"):
            ocean_token.mint(w.address, amt_distribute, {"from": wallet})


@pytest.fixture
def config():
    return get_config_dict()


@pytest.fixture
def publisher_ocean():
    return get_publisher_ocean_instance()


@pytest.fixture
def consumer_ocean():
    return get_consumer_ocean_instance()


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
def factory_deployer_wallet(config):
    return get_factory_deployer_wallet(config)


@pytest.fixture
def ocean_address(config) -> str:
    return get_address_of_type(config, "Ocean")


@pytest.fixture
def ocean_token(config, ocean_address) -> Datatoken:
    connect_to_network("development")
    return Datatoken(config, ocean_address)


@pytest.fixture
def factory_router(config):
    return FactoryRouter(config, get_address_of_type(config, "Router"))


@pytest.fixture
def data_nft_factory(config):
    return DataNFTFactoryContract(config, get_address_of_type(config, "ERC721Factory"))


@pytest.fixture
def provider_wallet():
    return get_provider_wallet()


@pytest.fixture
def file1():
    return get_file1()


@pytest.fixture
def file2():
    return get_file2()


@pytest.fixture
def file3():
    return get_file3()
