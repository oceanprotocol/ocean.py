#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Tuple

import pytest

from ocean_lib.example_config import get_config_dict
from ocean_lib.models.data_nft import DataNFT
from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.models.datatoken1 import Datatoken1
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.ocean.util import get_address_of_type, send_ether, to_wei
from ocean_lib.web3_internal.contract_utils import get_contracts_addresses_all_networks
from tests.resources.helper_functions import (
    deploy_erc721_erc20,
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
    get_wallet,
    setup_logging,
)

_NETWORK = "ganache"

setup_logging()


@pytest.fixture(autouse=True)
def setup_all(request, config, ocean_token):
    # a test can skip setup_all() via decorator "@pytest.mark.nosetup_all"
    if "nosetup_all" in request.keywords:
        return

    wallet = get_ganache_wallet()

    if not wallet:
        return

    if not get_contracts_addresses_all_networks(config):
        print("Can not find adddresses.")
        return

    balance = config["web3_instance"].eth.get_balance(wallet.address)
    assert balance >= to_wei(10), "Need more ETH"

    amt_distribute = to_wei(1000)
    ocean_token.mint(wallet, to_wei(2000), {"from": wallet})

    for w in (get_publisher_wallet(), get_consumer_wallet()):
        balance = config["web3_instance"].eth.get_balance(w.address)

        if balance < to_wei(2):
            send_ether(config, wallet, w.address, to_wei(4))

        if ocean_token.balanceOf(w) < to_wei(100):
            ocean_token.mint(w, amt_distribute, {"from": wallet})


@pytest.fixture
def config():
    return get_config_dict()


@pytest.fixture
def publisher_ocean():
    return get_publisher_ocean_instance()


@pytest.fixture
def basic_asset(publisher_ocean, publisher_wallet):
    name = "Branin dataset"
    url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"

    (data_nft, datatoken, ddo) = publisher_ocean.assets.create_url_asset(
        name, url, {"from": publisher_wallet}
    )

    assert ddo.nft["name"] == name
    assert len(ddo.datatokens) == 1

    return (data_nft, datatoken, ddo)


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
def ocean_token(config, ocean_address) -> Datatoken1:
    return Datatoken1(config, ocean_address)


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


@pytest.fixture
def FRE(config) -> FixedRateExchange:
    return FixedRateExchange(config, get_address_of_type(config, "FixedPrice"))


@pytest.fixture
def data_nft(config, publisher_wallet) -> DataNFT:
    return deploy_erc721_erc20(config, publisher_wallet)


@pytest.fixture
def data_NFT_and_DT(config, publisher_wallet) -> Tuple[DataNFT, Datatoken1]:
    return deploy_erc721_erc20(config, publisher_wallet, publisher_wallet)


@pytest.fixture
def DT(data_NFT_and_DT) -> Datatoken1:
    (_, DT) = data_NFT_and_DT
    return DT


# aliases
@pytest.fixture
def OCEAN(ocean_token) -> Datatoken1:
    return ocean_token


@pytest.fixture
def alice(publisher_wallet):
    return publisher_wallet


@pytest.fixture
def bob(consumer_wallet):
    return consumer_wallet


@pytest.fixture
def carlos():
    return get_wallet(8)


@pytest.fixture
def dan():
    return get_wallet(7)
